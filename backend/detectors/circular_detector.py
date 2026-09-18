"""
Explainable Circular Transfer / Round-Tripping Detector:
Detects directed cycles where funds circulate through one or more intermediate accounts and return to the origin.
"""
from typing import List, Dict, Any, Set, Tuple
import networkx as nx
from backend.graph.financial_graph import FinancialMultiGraph
from backend.models.findings import PatternFinding, PatternType, PatternSeverity, EvidenceItem


class CircularTransferDetector:
    """
    Identifies closed loops / cycles in the financial multigraph ($A \\to B \\to C \\to A$)
    representing round-tripping, fictitious trade cycling, or tax avoidance schemes.
    """

    def __init__(self, max_cycle_length: int = 6):
        self.max_cycle_length = max_cycle_length

    def detect(self, graph: FinancialMultiGraph) -> List[PatternFinding]:
        findings: List[PatternFinding] = []
        if graph.get_node_count() < 2:
            return findings

        # Simple directed graph for simple_cycles
        simple_digraph = nx.DiGraph()
        for u, v, data in graph.graph.edges(data=True):
            simple_digraph.add_edge(u, v)

        try:
            raw_cycles = list(nx.simple_cycles(simple_digraph))
        except Exception:
            return findings

        seen_cycles: Set[Tuple[str, ...]] = set()

        for cycle in raw_cycles:
            if len(cycle) < 2 or len(cycle) > self.max_cycle_length:
                continue

            # Canonicalize cycle representation to avoid duplicate permutations
            min_idx = cycle.index(min(cycle))
            canonical_cycle = tuple(cycle[min_idx:] + cycle[:min_idx])
            if canonical_cycle in seen_cycles:
                continue
            seen_cycles.add(canonical_cycle)

            # Find matching transactions along cycle
            cycle_nodes = list(canonical_cycle) + [canonical_cycle[0]]
            cycle_txs = []
            cycle_amounts = []
            cycle_timestamps = []

            for i in range(len(cycle_nodes) - 1):
                u = cycle_nodes[i]
                v = cycle_nodes[i + 1]
                # Pick most recent edge u -> v
                edges = graph.graph.get_edge_data(u, v)
                if edges:
                    # Pick edge with max amount or latest timestamp
                    edge_key, edge_data = list(edges.items())[0]
                    tx_id = edge_data.get("transaction_id", edge_key)
                    if tx_id in graph.transactions:
                        tx_obj = graph.transactions[tx_id]
                        cycle_txs.append(tx_obj)
                        cycle_amounts.append(tx_obj.amount)
                        cycle_timestamps.append(tx_obj.timestamp)

            if len(cycle_txs) != len(cycle_nodes) - 1:
                continue

            tx_ids = [tx.transaction_id for tx in cycle_txs]
            total_vol = sum(cycle_amounts)
            start_amt = cycle_amounts[0]
            returned_amt = cycle_amounts[-1]
            return_pct = round((returned_amt / start_amt) * 100.0, 2) if start_amt > 0 else 100.0

            time_diff = (max(cycle_timestamps) - min(cycle_timestamps)).total_seconds() / 3600.0

            evidence = EvidenceItem(
                evidence_id=f"EV_CYC_{len(findings)+1:03d}",
                finding_title=f"Circular round-tripping loop involving {len(canonical_cycle)} entities",
                pattern_type=PatternType.CIRCULAR_TRANSFER,
                involved_accounts=list(canonical_cycle),
                transaction_ids=tx_ids,
                timestamps=cycle_timestamps,
                amounts_inr=cycle_amounts,
                dwell_time_minutes=round(time_diff * 60.0, 1),
                retention_percentage=return_pct,
                narrative_explanation=(
                    f"Identified closed cycle: {' → '.join(cycle_nodes)} moving ₹{start_amt:,.2f} "
                    f"returning ₹{returned_amt:,.2f} ({return_pct}% return ratio) over {time_diff:.1f} hours."
                ),
            )

            finding = PatternFinding(
                pattern_id=f"PAT_CYC_{len(findings)+1:03d}",
                pattern_type=PatternType.CIRCULAR_TRANSFER,
                severity=PatternSeverity.CRITICAL if len(canonical_cycle) <= 3 else PatternSeverity.HIGH,
                title=f"Circular Transfer Loop ({len(canonical_cycle)} Accounts)",
                description=(
                    f"Funds circulate in a closed loop through {len(canonical_cycle)} accounts: "
                    f"{' → '.join(cycle_nodes)}, indicating potential round-tripping or fictitious settlement."
                ),
                accounts_involved=list(canonical_cycle),
                transaction_ids=tx_ids,
                total_volume_inr=total_vol,
                metrics={
                    "cycle_length": len(canonical_cycle),
                    "cycle_path": cycle_nodes,
                    "cycle_duration_hours": round(time_diff, 2),
                    "return_percentage": return_pct,
                    "volume_inr": total_vol,
                },
                evidence=[evidence],
                confidence_score=0.92,
            )
            findings.append(finding)

        return findings
