"""
Explainable Rapid Movement & Mule Velocity Detector:
Detects rapid pass-through / gatekeeper mule activity where funds are forwarded within minutes with minimal dwell time.
"""
from typing import List, Dict, Any
from backend.graph.financial_graph import FinancialMultiGraph
from backend.models.findings import PatternFinding, PatternType, PatternSeverity, EvidenceItem


class RapidMovementDetector:
    """
    Detects accounts receiving substantial funds and forwarding a high percentage (>80%)
    within a short dwell window (< 60 minutes), characteristic of money mule pass-through accounts.
    """

    def __init__(self, max_dwell_minutes: float = 60.0, min_forwarding_ratio: float = 0.75, min_amount_inr: float = 25000.0):
        self.max_dwell_minutes = max_dwell_minutes
        self.min_forwarding_ratio = min_forwarding_ratio
        self.min_amount_inr = min_amount_inr

    def detect(self, graph: FinancialMultiGraph) -> List[PatternFinding]:
        findings: List[PatternFinding] = []
        accounts = graph.get_accounts()

        for acc in accounts:
            in_txs = graph.get_incoming_transactions(acc)
            out_txs = graph.get_outgoing_transactions(acc)

            if not in_txs or not out_txs:
                continue

            for in_tx in in_txs:
                if in_tx.amount < self.min_amount_inr:
                    continue

                for out_tx in out_txs:
                    if out_tx.timestamp < in_tx.timestamp:
                        continue

                    dwell_seconds = (out_tx.timestamp - in_tx.timestamp).total_seconds()
                    dwell_minutes = dwell_seconds / 60.0

                    if dwell_minutes > self.max_dwell_minutes:
                        continue

                    forwarding_ratio = out_tx.amount / in_tx.amount
                    # Forwarding ratio should be between min_forwarding_ratio and 1.25 (allowing minor variations)
                    if forwarding_ratio < self.min_forwarding_ratio or forwarding_ratio > 1.25:
                        continue

                    retained_amount = in_tx.amount - out_tx.amount
                    retained_pct = round((out_tx.amount / in_tx.amount) * 100.0, 1)

                    evidence = EvidenceItem(
                        evidence_id=f"EV_RAP_{len(findings)+1:03d}",
                        finding_title=f"Rapid pass-through at {acc} in {dwell_minutes:.1f} mins",
                        pattern_type=PatternType.RAPID_MOVEMENT,
                        involved_accounts=[in_tx.sender_account, acc, out_tx.receiver_account],
                        transaction_ids=[in_tx.transaction_id, out_tx.transaction_id],
                        timestamps=[in_tx.timestamp, out_tx.timestamp],
                        amounts_inr=[in_tx.amount, out_tx.amount],
                        dwell_time_minutes=round(dwell_minutes, 1),
                        retention_percentage=retained_pct,
                        narrative_explanation=(
                            f"Account {acc} received ₹{in_tx.amount:,.2f} from {in_tx.sender_account} via {in_tx.channel.value} "
                            f"and forwarded ₹{out_tx.amount:,.2f} ({retained_pct}% forwarded) to {out_tx.receiver_account} "
                            f"after only {dwell_minutes:.1f} minutes of dwell time."
                        ),
                    )

                    finding = PatternFinding(
                        pattern_id=f"PAT_RAP_{len(findings)+1:03d}",
                        pattern_type=PatternType.RAPID_MOVEMENT,
                        severity=PatternSeverity.HIGH if dwell_minutes < 15.0 else PatternSeverity.MEDIUM,
                        title=f"Rapid Inflow-Outflow Velocity ({acc})",
                        description=(
                            f"High-velocity fund forwarding detected at account {acc}: "
                            f"₹{in_tx.amount:,.2f} received and ₹{out_tx.amount:,.2f} forwarded in {dwell_minutes:.1f} minutes."
                        ),
                        accounts_involved=[in_tx.sender_account, acc, out_tx.receiver_account],
                        transaction_ids=[in_tx.transaction_id, out_tx.transaction_id],
                        total_volume_inr=in_tx.amount + out_tx.amount,
                        metrics={
                            "mule_account": acc,
                            "inflow_amount_inr": in_tx.amount,
                            "outflow_amount_inr": out_tx.amount,
                            "dwell_time_minutes": round(dwell_minutes, 1),
                            "forwarding_ratio": round(forwarding_ratio, 3),
                            "velocity_rating": "ULTRA_HIGH" if dwell_minutes < 10 else "HIGH",
                        },
                        evidence=[evidence],
                        confidence_score=0.89,
                    )
                    findings.append(finding)

        return findings
