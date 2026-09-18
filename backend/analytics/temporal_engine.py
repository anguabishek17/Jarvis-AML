"""
Temporal Intelligence Engine:
Analyzes chronological transaction progression and partitions the investigation into distinct temporal stages:
INJECTION -> DISPERSION -> LAYERING -> CONVERGENCE -> SINK.
"""
from typing import List, Dict, Any
from datetime import datetime
from backend.graph.financial_graph import FinancialMultiGraph
from backend.models.findings import AccountRoleHypothesis, AccountRole, PatternFinding


class TemporalStage:
    def __init__(
        self,
        stage_id: str,
        stage_name: str,
        start_time: datetime,
        end_time: datetime,
        accounts_active: List[str],
        transaction_ids: List[str],
        volume_inr: float,
        narrative: str,
        connected_patterns: List[str],
    ):
        self.stage_id = stage_id
        self.stage_name = stage_name
        self.start_time = start_time
        self.end_time = end_time
        self.accounts_active = accounts_active
        self.transaction_ids = transaction_ids
        self.volume_inr = volume_inr
        self.narrative = narrative
        self.connected_patterns = connected_patterns

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage_id": self.stage_id,
            "stage_name": self.stage_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "time_range_display": f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')} IST",
            "accounts_active": self.accounts_active,
            "transaction_ids": self.transaction_ids,
            "volume_inr": round(self.volume_inr, 2),
            "narrative": self.narrative,
            "connected_patterns": self.connected_patterns,
        }


class TemporalEngine:
    """
    Deconstructs the transaction graph timeline into sequential lifecycle stages.
    """

    def analyze_stages(
        self,
        graph: FinancialMultiGraph,
        roles: Dict[str, AccountRoleHypothesis],
        findings: List[PatternFinding] = None,
    ) -> List[Dict[str, Any]]:
        all_txs = sorted(graph.get_all_transactions(), key=lambda x: x.timestamp)
        if not all_txs:
            return []

        if len(all_txs) <= 2:
            # Simple single stage
            stage = TemporalStage(
                stage_id="STAGE_01",
                stage_name="INJECTION",
                start_time=all_txs[0].timestamp,
                end_time=all_txs[-1].timestamp,
                accounts_active=list(set([tx.sender_account for tx in all_txs] + [tx.receiver_account for tx in all_txs])),
                transaction_ids=[tx.transaction_id for tx in all_txs],
                volume_inr=sum(tx.amount for tx in all_txs),
                narrative=f"Observed {len(all_txs)} transactions moving ₹{sum(tx.amount for tx in all_txs):,.2f}.",
                connected_patterns=[],
            )
            return [stage.to_dict()]

        # Identify stage transitions by role of sender/receiver and time intervals
        injection_txs = []
        dispersion_txs = []
        layering_txs = []
        convergence_txs = []
        sink_txs = []

        for tx in all_txs:
            sender_role = roles.get(tx.sender_account, None)
            receiver_role = roles.get(tx.receiver_account, None)

            s_role_val = sender_role.probable_role if sender_role else AccountRole.LEGITIMATE
            r_role_val = receiver_role.probable_role if receiver_role else AccountRole.LEGITIMATE

            if s_role_val == AccountRole.ORIGINATOR:
                if r_role_val == AccountRole.DISPERSER or "SMURF" in tx.receiver_account:
                    dispersion_txs.append(tx)
                else:
                    injection_txs.append(tx)
            elif s_role_val == AccountRole.DISPERSER or (s_role_val == AccountRole.MULE and r_role_val == AccountRole.MULE):
                if r_role_val == AccountRole.MULE or "SMURF" in tx.receiver_account:
                    dispersion_txs.append(tx)
                else:
                    layering_txs.append(tx)
            elif r_role_val == AccountRole.AGGREGATOR:
                convergence_txs.append(tx)
            elif r_role_val == AccountRole.SINK or s_role_val == AccountRole.AGGREGATOR:
                sink_txs.append(tx)
            else:
                layering_txs.append(tx)

        # Build Stage objects chronologically
        stages: List[TemporalStage] = []
        stage_groups = [
            ("INJECTION", injection_txs, "Initial placement/funds entry into source accounts"),
            ("DISPERSION", dispersion_txs, "Structuring and fan-out distribution across smurf accounts"),
            ("LAYERING", layering_txs, "Rapid multi-hop transfers through intermediary mule accounts"),
            ("CONVERGENCE", convergence_txs, "Aggregation and funneling of dispersed funds into master accounts"),
            ("SINK", sink_txs, "Final integration and settlement into terminal sink accounts"),
        ]

        stage_idx = 1
        for name, txs, desc in stage_groups:
            if not txs:
                continue

            start_t = min(tx.timestamp for tx in txs)
            end_t = max(tx.timestamp for tx in txs)
            active_accs = list(set([tx.sender_account for tx in txs] + [tx.receiver_account for tx in txs]))
            tx_ids = [tx.transaction_id for tx in txs]
            vol = sum(tx.amount for tx in txs)

            # Find matching patterns
            patterns = []
            if findings:
                for f in findings:
                    if any(acc in active_accs for acc in f.accounts_involved):
                        patterns.append(f.pattern_type.value)

            stage_obj = TemporalStage(
                stage_id=f"STAGE_{stage_idx:02d}",
                stage_name=name,
                start_time=start_t,
                end_time=end_t,
                accounts_active=active_accs,
                transaction_ids=tx_ids,
                volume_inr=vol,
                narrative=f"{desc}: ₹{vol:,.2f} moved across {len(active_accs)} accounts in {len(txs)} transactions.",
                connected_patterns=list(set(patterns)),
            )
            stages.append(stage_obj)
            stage_idx += 1

        # If empty stages fallback to time-based split
        if not stages:
            chunk_size = max(1, len(all_txs) // 3)
            for i in range(0, len(all_txs), chunk_size):
                chunk = all_txs[i:i+chunk_size]
                if not chunk:
                    continue
                start_t = chunk[0].timestamp
                end_t = chunk[-1].timestamp
                active_accs = list(set([tx.sender_account for tx in chunk] + [tx.receiver_account for tx in chunk]))
                vol = sum(tx.amount for tx in chunk)
                stage_obj = TemporalStage(
                    stage_id=f"STAGE_{len(stages)+1:02d}",
                    stage_name=f"STAGE_{len(stages)+1:02d}",
                    start_time=start_t,
                    end_time=end_t,
                    accounts_active=active_accs,
                    transaction_ids=[tx.transaction_id for tx in chunk],
                    volume_inr=vol,
                    narrative=f"Stage {len(stages)+1}: ₹{vol:,.2f} moved across {len(active_accs)} accounts.",
                    connected_patterns=[],
                )
                stages.append(stage_obj)

        return [s.to_dict() for s in stages]
