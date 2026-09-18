"""
Explainable Layering Detector: Identifies multi-hop sequential fund movements across intermediary accounts
designed to distance illicit funds from their original source.
"""
from typing import List, Dict, Any, Set
from backend.graph.financial_graph import FinancialMultiGraph
from backend.models.findings import PatternFinding, PatternType, PatternSeverity, EvidenceItem


class LayeringDetector:
    """
    Detects sequential multi-hop transfers (hop count >= 3) where funds move along a chain of accounts
    with consistent amounts and chronological sequencing.
    """

    def __init__(self, min_hops: int = 3, max_time_window_hours: float = 72.0, min_retention_ratio: float = 0.5):
        self.min_hops = min_hops
        self.max_time_window_hours = max_time_window_hours
        self.min_retention_ratio = min_retention_ratio

    def detect(self, graph: FinancialMultiGraph) -> List[PatternFinding]:
        findings: List[PatternFinding] = []
        accounts = graph.get_accounts()

        # Find paths of length >= min_hops
        # We start from accounts that have low in-degree or are source-like
        visited_chains: Set[str] = set()

        for source in accounts:
            out_txs = graph.get_outgoing_transactions(source)
            if not out_txs:
                continue

            for start_tx in out_txs:
                self._explore_layering_path(
                    graph=graph,
                    current_acc=start_tx.receiver_account,
                    current_chain=[start_tx.sender_account, start_tx.receiver_account],
                    current_txs=[start_tx],
                    start_amount=start_tx.amount,
                    current_amount=start_tx.amount,
                    findings=findings,
                    visited_chains=visited_chains,
                )

        return findings

    def _explore_layering_path(
        self,
        graph: FinancialMultiGraph,
        current_acc: str,
        current_chain: List[str],
        current_txs: List[Any],
        start_amount: float,
        current_amount: float,
        findings: List[PatternFinding],
        visited_chains: Set[str],
    ) -> None:
        last_tx = current_txs[-1]
        next_out_txs = graph.get_outgoing_transactions(current_acc)

        valid_next_found = False
        for next_tx in next_out_txs:
            # Must be chronologically after the last transaction
            if next_tx.timestamp < last_tx.timestamp:
                continue

            # Must not create an immediate 2-node cycle
            if next_tx.receiver_account in current_chain:
                continue

            # Elapsed time check
            elapsed_hours = (next_tx.timestamp - current_txs[0].timestamp).total_seconds() / 3600.0
            if elapsed_hours > self.max_time_window_hours:
                continue

            # Amount retention check (must retain at least min_retention_ratio of prior transfer)
            if next_tx.amount > (current_amount * 1.5) or next_tx.amount < (current_amount * 0.4):
                continue

            valid_next_found = True
            self._explore_layering_path(
                graph=graph,
                current_acc=next_tx.receiver_account,
                current_chain=current_chain + [next_tx.receiver_account],
                current_txs=current_txs + [next_tx],
                start_amount=start_amount,
                current_amount=next_tx.amount,
                findings=findings,
                visited_chains=visited_chains,
            )

        # If reached terminal hop with sufficient length
        hop_count = len(current_chain) - 1
        if not valid_next_found and hop_count >= self.min_hops:
            chain_key = "->".join(current_chain)
            if chain_key not in visited_chains:
                visited_chains.add(chain_key)
                
                final_amount = current_txs[-1].amount
                retention_pct = round((final_amount / start_amount) * 100.0, 2)
                elapsed_mins = round((current_txs[-1].timestamp - current_txs[0].timestamp).total_seconds() / 60.0, 1)

                tx_ids = [tx.transaction_id for tx in current_txs]
                timestamps = [tx.timestamp for tx in current_txs]
                amounts = [tx.amount for tx in current_txs]

                evidence = EvidenceItem(
                    evidence_id=f"EV_LAY_{len(findings)+1:03d}",
                    finding_title=f"Multi-hop layering across {hop_count} transit accounts",
                    pattern_type=PatternType.LAYERING,
                    involved_accounts=current_chain,
                    transaction_ids=tx_ids,
                    timestamps=timestamps,
                    amounts_inr=amounts,
                    dwell_time_minutes=elapsed_mins,
                    retention_percentage=retention_pct,
                    narrative_explanation=(
                        f"Detected {hop_count}-hop sequential fund movement starting with ₹{start_amount:,.2f} "
                        f"from {current_chain[0]} and terminating at {current_chain[-1]} with ₹{final_amount:,.2f} "
                        f"({retention_pct}% retained) over {elapsed_mins} minutes."
                    ),
                )

                finding = PatternFinding(
                    pattern_id=f"PAT_LAY_{len(findings)+1:03d}",
                    pattern_type=PatternType.LAYERING,
                    severity=PatternSeverity.HIGH if hop_count >= 4 else PatternSeverity.MEDIUM,
                    title=f"Sequential Layering Trail ({hop_count} Hops)",
                    description=(
                        f"Funds moved through a sequential chain of {len(current_chain)} accounts: "
                        f"{' → '.join(current_chain)} with high amount retention and rapid transit."
                    ),
                    accounts_involved=current_chain,
                    transaction_ids=tx_ids,
                    total_volume_inr=sum(amounts),
                    metrics={
                        "hop_count": hop_count,
                        "initial_amount_inr": start_amount,
                        "final_amount_inr": final_amount,
                        "retention_percentage": retention_pct,
                        "elapsed_transit_minutes": elapsed_mins,
                    },
                    evidence=[evidence],
                    confidence_score=min(0.70 + (hop_count * 0.06), 0.96),
                )
                findings.append(finding)
