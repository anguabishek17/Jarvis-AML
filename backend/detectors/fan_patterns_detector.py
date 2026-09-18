"""
Explainable Fan-In (Aggregation/Funneling) and Fan-Out (Dispersion/Smurfing) Detectors.
"""
from typing import List, Dict, Any
from backend.graph.financial_graph import FinancialMultiGraph
from backend.models.findings import PatternFinding, PatternType, PatternSeverity, EvidenceItem


class FanPatternsDetector:
    """
    Detects:
    1. Fan-In: Multiple distinct accounts sending funds into a single aggregator account within a time window.
    2. Fan-Out: A single account dispersing structured funds to multiple distinct recipient accounts.
    """

    def __init__(self, min_fan_count: int = 3, time_window_hours: float = 48.0):
        self.min_fan_count = min_fan_count
        self.time_window_hours = time_window_hours

    def detect_fan_in(self, graph: FinancialMultiGraph) -> List[PatternFinding]:
        findings: List[PatternFinding] = []
        accounts = graph.get_accounts()

        for aggregator in accounts:
            in_txs = graph.get_incoming_transactions(aggregator)
            if len(in_txs) < self.min_fan_count:
                continue

            # Group distinct senders
            senders = list(set(tx.sender_account for tx in in_txs))
            if len(senders) < self.min_fan_count:
                continue

            tx_ids = [tx.transaction_id for tx in in_txs]
            timestamps = [tx.timestamp for tx in in_txs]
            amounts = [tx.amount for tx in in_txs]
            total_vol = sum(amounts)

            # Check time span
            time_span_hours = (max(timestamps) - min(timestamps)).total_seconds() / 3600.0
            if time_span_hours > self.time_window_hours and len(in_txs) < 5:
                continue

            evidence = EvidenceItem(
                evidence_id=f"EV_FAN_IN_{len(findings)+1:03d}",
                finding_title=f"Funnel aggregation from {len(senders)} sources into {aggregator}",
                pattern_type=PatternType.FAN_IN,
                involved_accounts=senders + [aggregator],
                transaction_ids=tx_ids,
                timestamps=timestamps,
                amounts_inr=amounts,
                dwell_time_minutes=round(time_span_hours * 60.0, 1),
                retention_percentage=100.0,
                narrative_explanation=(
                    f"Account {aggregator} received {len(in_txs)} incoming transfers totalling ₹{total_vol:,.2f} "
                    f"from {len(senders)} distinct sender accounts within {time_span_hours:.1f} hours."
                ),
            )

            finding = PatternFinding(
                pattern_id=f"PAT_FAN_IN_{len(findings)+1:03d}",
                pattern_type=PatternType.FAN_IN,
                severity=PatternSeverity.HIGH if len(senders) >= 4 else PatternSeverity.MEDIUM,
                title=f"Fan-In Aggregation ({len(senders)} Feeder Accounts → {aggregator})",
                description=(
                    f"Concentration of funds detected: {len(senders)} accounts routed a combined total of ₹{total_vol:,.2f} "
                    f"into aggregator {aggregator}."
                ),
                accounts_involved=senders + [aggregator],
                transaction_ids=tx_ids,
                total_volume_inr=total_vol,
                metrics={
                    "aggregator_account": aggregator,
                    "feeder_count": len(senders),
                    "transaction_count": len(in_txs),
                    "total_aggregated_inr": total_vol,
                    "time_span_hours": round(time_span_hours, 2),
                },
                evidence=[evidence],
                confidence_score=0.88,
            )
            findings.append(finding)

        return findings

    def detect_fan_out(self, graph: FinancialMultiGraph) -> List[PatternFinding]:
        findings: List[PatternFinding] = []
        accounts = graph.get_accounts()

        for disperser in accounts:
            out_txs = graph.get_outgoing_transactions(disperser)
            if len(out_txs) < self.min_fan_count:
                continue

            receivers = list(set(tx.receiver_account for tx in out_txs))
            if len(receivers) < self.min_fan_count:
                continue

            tx_ids = [tx.transaction_id for tx in out_txs]
            timestamps = [tx.timestamp for tx in out_txs]
            amounts = [tx.amount for tx in out_txs]
            total_vol = sum(amounts)

            time_span_hours = (max(timestamps) - min(timestamps)).total_seconds() / 3600.0
            if time_span_hours > self.time_window_hours and len(out_txs) < 5:
                continue

            evidence = EvidenceItem(
                evidence_id=f"EV_FAN_OUT_{len(findings)+1:03d}",
                finding_title=f"Dispersion from {disperser} across {len(receivers)} beneficiary accounts",
                pattern_type=PatternType.FAN_OUT,
                involved_accounts=[disperser] + receivers,
                transaction_ids=tx_ids,
                timestamps=timestamps,
                amounts_inr=amounts,
                dwell_time_minutes=round(time_span_hours * 60.0, 1),
                retention_percentage=100.0,
                narrative_explanation=(
                    f"Account {disperser} dispersed ₹{total_vol:,.2f} across {len(receivers)} distinct recipient accounts "
                    f"via {len(out_txs)} transactions within {time_span_hours:.1f} hours."
                ),
            )

            finding = PatternFinding(
                pattern_id=f"PAT_FAN_OUT_{len(findings)+1:03d}",
                pattern_type=PatternType.FAN_OUT,
                severity=PatternSeverity.HIGH if len(receivers) >= 4 else PatternSeverity.MEDIUM,
                title=f"Fan-Out Dispersion ({disperser} → {len(receivers)} Beneficiaries)",
                description=(
                    f"Dispersion pattern detected: Single account {disperser} split and transferred ₹{total_vol:,.2f} "
                    f"across {len(receivers)} distinct recipient accounts."
                ),
                accounts_involved=[disperser] + receivers,
                transaction_ids=tx_ids,
                total_volume_inr=total_vol,
                metrics={
                    "disperser_account": disperser,
                    "beneficiary_count": len(receivers),
                    "transaction_count": len(out_txs),
                    "total_dispersed_inr": total_vol,
                    "time_span_hours": round(time_span_hours, 2),
                },
                evidence=[evidence],
                confidence_score=0.87,
            )
            findings.append(finding)

        return findings

    def detect_all(self, graph: FinancialMultiGraph) -> List[PatternFinding]:
        return self.detect_fan_in(graph) + self.detect_fan_out(graph)
