"""
Attack Path Reconstruction Engine:
Extracts end-to-end suspicious money-flow paths from originators through intermediaries to sinks
using constrained depth-first search with chronological and amount retention bounds.
"""
from typing import List, Dict, Any, Set, Tuple
from datetime import datetime
from backend.graph.financial_graph import FinancialMultiGraph
from backend.models.findings import AttackPath, PatternType


class AttackPathEngine:
    """
    Reconstructs end-to-end money trail paths from Originator to Sink accounts.
    Calculates retention %, hop counts, transit durations, and associated patterns.
    """

    def __init__(self, max_hops: int = 8, min_hops: int = 2, max_transit_hours: float = 72.0):
        self.max_hops = max_hops
        self.min_hops = min_hops
        self.max_transit_hours = max_transit_hours

    def reconstruct_paths(self, graph: FinancialMultiGraph, pattern_types_by_account: Dict[str, Set[PatternType]] = None) -> List[AttackPath]:
        if pattern_types_by_account is None:
            pattern_types_by_account = {}

        accounts = graph.get_accounts()
        if not accounts:
            return []

        # Identify potential originators (high out-degree, low in-degree)
        candidate_sources = []
        candidate_sinks = []

        for acc in accounts:
            metrics = graph.get_account_metrics(acc)
            if metrics["in_degree"] == 0 or (metrics["out_degree"] > 0 and metrics["inflow_total"] < metrics["outflow_total"] * 0.5):
                candidate_sources.append(acc)
            if metrics["out_degree"] == 0 or (metrics["in_degree"] > 0 and metrics["outflow_total"] < metrics["inflow_total"] * 0.5):
                candidate_sinks.append(acc)

        # If no strict candidates, fallback to all accounts with out_degree > 0 as sources
        if not candidate_sources:
            candidate_sources = [acc for acc in accounts if graph.get_account_metrics(acc)["out_degree"] > 0]
        if not candidate_sinks:
            candidate_sinks = [acc for acc in accounts if graph.get_account_metrics(acc)["in_degree"] > 0]

        extracted_paths: List[AttackPath] = []
        seen_path_keys: Set[str] = set()

        for src in candidate_sources:
            for sink in candidate_sinks:
                if src == sink:
                    continue

                self._find_paths_between(
                    graph=graph,
                    current_node=src,
                    target_node=sink,
                    current_path=[src],
                    current_txs=[],
                    extracted_paths=extracted_paths,
                    seen_path_keys=seen_path_keys,
                    pattern_types_by_account=pattern_types_by_account,
                )

        # Rank paths by volume * hop_count * retention
        for idx, p in enumerate(sorted(extracted_paths, key=lambda x: (x.hop_count * x.total_inflow_inr * (x.retention_percentage / 100.0)), reverse=True), 1):
            p.risk_rank = idx
            p.path_id = f"PATH_{idx:03d}"

        return extracted_paths

    def _find_paths_between(
        self,
        graph: FinancialMultiGraph,
        current_node: str,
        target_node: str,
        current_path: List[str],
        current_txs: List[Any],
        extracted_paths: List[AttackPath],
        seen_path_keys: Set[str],
        pattern_types_by_account: Dict[str, Set[PatternType]],
    ) -> None:
        if len(current_path) - 1 > self.max_hops:
            return

        if current_node == target_node and len(current_path) - 1 >= self.min_hops:
            path_key = "->".join(current_path)
            if path_key in seen_path_keys:
                return
            seen_path_keys.add(path_key)

            initial_amt = current_txs[0].amount
            final_amt = current_txs[-1].amount
            retention_pct = round((final_amt / initial_amt) * 100.0, 2) if initial_amt > 0 else 100.0
            retained_amt = round(initial_amt - final_amt, 2)

            start_t = current_txs[0].timestamp
            end_t = current_txs[-1].timestamp
            elapsed_mins = round((end_t - start_t).total_seconds() / 60.0, 1)

            # Collect patterns along path
            path_patterns = set()
            for acc in current_path:
                if acc in pattern_types_by_account:
                    path_patterns.update(pattern_types_by_account[acc])

            attack_path = AttackPath(
                path_id=f"PATH_TMP_{len(extracted_paths)+1}",
                source_account=current_path[0],
                destination_account=current_path[-1],
                intermediate_accounts=current_path[1:-1],
                account_sequence=current_path,
                transaction_ids=[tx.transaction_id for tx in current_txs],
                hop_count=len(current_path) - 1,
                total_inflow_inr=initial_amt,
                total_outflow_inr=final_amt,
                retained_amount_inr=retained_amt,
                retention_percentage=retention_pct,
                start_time=start_t,
                end_time=end_t,
                elapsed_minutes=elapsed_mins,
                associated_patterns=list(path_patterns),
                risk_rank=len(extracted_paths) + 1,
            )
            extracted_paths.append(attack_path)
            return

        out_txs = graph.get_outgoing_transactions(current_node)
        for tx in out_txs:
            next_node = tx.receiver_account
            if next_node in current_path:
                continue

            if current_txs:
                if tx.timestamp < current_txs[-1].timestamp:
                    continue
                elapsed_hrs = (tx.timestamp - current_txs[0].timestamp).total_seconds() / 3600.0
                if elapsed_hrs > self.max_transit_hours:
                    continue

            self._find_paths_between(
                graph=graph,
                current_node=next_node,
                target_node=target_node,
                current_path=current_path + [next_node],
                current_txs=current_txs + [tx],
                extracted_paths=extracted_paths,
                seen_path_keys=seen_path_keys,
                pattern_types_by_account=pattern_types_by_account,
            )
