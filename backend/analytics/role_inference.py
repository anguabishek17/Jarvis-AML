"""
Account Role Inference Engine:
Infers probable operational roles (ORIGINATOR, MULE, DISPERSER, AGGREGATOR, SINK, LEGITIMATE)
using observable network metrics, forwarding ratios, dwell times, and pattern participation.
Hypotheses for human investigator guidance, NOT criminal verdicts.
"""
from typing import List, Dict, Any, Set
from backend.graph.financial_graph import FinancialMultiGraph
from backend.models.findings import AccountRole, AccountRoleHypothesis, PatternFinding


class RoleInferenceEngine:
    """
    Evaluates account operational behavior against heuristic role signatures.
    Returns probable role, confidence score (0.0 to 1.0), and itemized evidence signals.
    """

    def infer_roles(
        self,
        graph: FinancialMultiGraph,
        findings: List[PatternFinding] = None,
    ) -> Dict[str, AccountRoleHypothesis]:
        if findings is None:
            findings = []

        # Map pattern participation by account
        pattern_map: Dict[str, List[str]] = {}
        for finding in findings:
            for acc in finding.accounts_involved:
                if acc not in pattern_map:
                    pattern_map[acc] = []
                pattern_map[acc].append(finding.pattern_type.value)

        centralities = graph.compute_centrality_metrics()
        results: Dict[str, AccountRoleHypothesis] = {}

        for acc in graph.get_accounts():
            metrics = graph.get_account_metrics(acc)
            cent = centralities.get(acc, {})
            betweenness = cent.get("betweenness", 0.0)
            in_txs = graph.get_incoming_transactions(acc)
            out_txs = graph.get_outgoing_transactions(acc)
            in_deg = len(in_txs)
            out_deg = len(out_txs)
            inflow = metrics["inflow_total"]
            outflow = metrics["outflow_total"]
            fwd_ratio = metrics["forwarding_ratio"]
            avg_dwell = metrics["avg_dwell_minutes"]
            patterns = pattern_map.get(acc, [])

            role, confidence, signals = self._classify_account(
                acc=acc,
                in_deg=in_deg,
                out_deg=out_deg,
                inflow=inflow,
                outflow=outflow,
                fwd_ratio=fwd_ratio,
                avg_dwell=avg_dwell,
                betweenness=betweenness,
                patterns=patterns,
            )

            hypothesis = AccountRoleHypothesis(
                account_id=acc,
                probable_role=role,
                confidence=round(confidence, 2),
                evidence_signals=signals,
                inflow_total_inr=inflow,
                outflow_total_inr=outflow,
                forwarding_ratio=round(fwd_ratio, 2),
                avg_dwell_minutes=round(avg_dwell, 1),
                in_degree=in_deg,
                out_degree=out_deg,
                betweenness_centrality=round(betweenness, 4),
                participating_patterns=list(set(patterns)),
            )
            results[acc] = hypothesis

        return results

    def _classify_account(
        self,
        acc: str,
        in_deg: int,
        out_deg: int,
        inflow: float,
        outflow: float,
        fwd_ratio: float,
        avg_dwell: float,
        betweenness: float,
        patterns: List[str],
    ) -> (AccountRole, float, List[str]):
        signals: List[str] = []

        # 1. ORIGINATOR check
        if (in_deg == 0 and out_deg > 0) or (inflow == 0 and outflow > 0):
            signals.append("Zero observed incoming transactions with significant outgoing volume")
            signals.append(f"Disbursed ₹{outflow:,.2f} into the transaction network")
            if out_deg > 2:
                signals.append(f"Multiple immediate distribution channels (Out-degree: {out_deg})")
            return AccountRole.ORIGINATOR, 0.92, signals

        # 2. SINK check
        if (out_deg == 0 and in_deg > 0) or (outflow == 0 and inflow > 0):
            signals.append("Zero downstream fund forwarding observed")
            signals.append(f"Final recipient of ₹{inflow:,.2f} cumulative funds")
            signals.append(f"Received funds across {in_deg} incoming transaction(s)")
            return AccountRole.SINK, 0.90, signals

        # 3. DISPERSER check (One to many)
        if out_deg >= 2 and out_deg >= in_deg * 2:
            signals.append(f"High dispersion ratio: {in_deg} incoming feeder(s) to {out_deg} outgoing beneficiaries")
            signals.append(f"Split ₹{inflow:,.2f} across multiple structured accounts")
            if "FAN_OUT" in patterns:
                signals.append("Active participant in detected Fan-Out pattern")
            return AccountRole.DISPERSER, 0.88, signals

        # 4. AGGREGATOR check (Many to one)
        if in_deg >= 2 and (out_deg == 0 or in_deg >= out_deg * 2):
            signals.append(f"High aggregation concentration: {in_deg} feeder accounts converging into {out_deg} downstream account(s)")
            signals.append(f"Aggregated ₹{inflow:,.2f} total funds")
            if "FAN_IN" in patterns:
                signals.append("Active participant in detected Fan-In funnel pattern")
            return AccountRole.AGGREGATOR, 0.89, signals

        # 5. MULE / TRANSIT check
        if fwd_ratio >= 0.75 and avg_dwell <= 60.0 and in_deg > 0 and out_deg > 0:
            signals.append(f"High forwarding velocity: {round(fwd_ratio*100, 1)}% of inflow forwarded")
            signals.append(f"Short intermediary dwell time: {avg_dwell:.1f} minutes average")
            if betweenness > 0.05:
                signals.append(f"Elevated network betweenness centrality ({betweenness:.3f})")
            if "RAPID_MOVEMENT" in patterns:
                signals.append("Participated in Rapid Movement / Velocity finding")
            if "LAYERING" in patterns:
                signals.append("Intermediate transit node in multi-hop layering trail")
            return AccountRole.MULE, 0.86, signals

        # 6. Secondary MULE / TRANSIT with looser dwell but high betweenness
        if fwd_ratio >= 0.60 and (betweenness >= 0.08 or "LAYERING" in patterns):
            signals.append(f"Forwarded {round(fwd_ratio*100, 1)}% of incoming funds")
            signals.append("Located centrally along critical multi-hop transfer path")
            return AccountRole.MULE, 0.78, signals

        # 7. Default to LEGITIMATE or General Participant
        if not patterns:
            signals.append("Normal transactional dwell times and balanced flow")
            signals.append("No participation in suspicious AML typologies")
            return AccountRole.LEGITIMATE, 0.85, signals
        else:
            signals.append("Moderate transactional activity within monitored network")
            return AccountRole.MULE, 0.65, signals
