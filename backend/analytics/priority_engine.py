"""
Investigation Priority Engine:
Calculates transparent 0-100 triage priority scores for accounts to guide human investigator attention.
Explicitly answers: "Which entity should the human investigator inspect first?"
"""
from typing import List, Dict, Any
from backend.graph.financial_graph import FinancialMultiGraph
from backend.models.findings import (
    InvestigationPriorityItem,
    AccountRoleHypothesis,
    AccountRole,
    PatternFinding,
    AttackPath,
)


class InvestigationPriorityEngine:
    """
    Transparent weighted triage prioritization:
    - Pattern severity & count (max 35)
    - Attack path appearances (max 25)
    - Network Centrality / Betweenness (max 15)
    - Transaction Volume (max 15)
    - Role Operational Hypothesis (max 10)
    """

    def compute_priority_rankings(
        self,
        graph: FinancialMultiGraph,
        roles: Dict[str, AccountRoleHypothesis],
        findings: List[PatternFinding],
        attack_paths: List[AttackPath],
    ) -> List[InvestigationPriorityItem]:
        accounts = graph.get_accounts()
        if not accounts:
            return []

        # 1. Map pattern count & types per account
        pattern_map: Dict[str, List[PatternFinding]] = {acc: [] for acc in accounts}
        for f in findings:
            for acc in f.accounts_involved:
                if acc in pattern_map:
                    pattern_map[acc].append(f)

        # 2. Map attack path appearances
        path_appearances: Dict[str, int] = {acc: 0 for acc in accounts}
        for path in attack_paths:
            for acc in path.account_sequence:
                if acc in path_appearances:
                    path_appearances[acc] += 1

        # 3. Max volume for normalization
        max_vol = max(
            [graph.get_account_metrics(acc)["inflow_total"] + graph.get_account_metrics(acc)["outflow_total"] for acc in accounts]
            + [1.0]
        )

        results: List[InvestigationPriorityItem] = []

        for acc in accounts:
            why_factors: List[str] = []
            score = 0.0

            # --- A. Pattern Factor (max 35) ---
            acc_patterns = pattern_map.get(acc, [])
            unique_pat_types = set(p.pattern_type.value for p in acc_patterns)
            pat_score = min(len(acc_patterns) * 9.0 + len(unique_pat_types) * 4.0, 35.0)
            score += pat_score
            if acc_patterns:
                why_factors.append(f"Participated in {len(acc_patterns)} suspicious patterns ({', '.join(unique_pat_types)}) (+{int(pat_score)} pts)")

            # --- B. Path Appearances (max 25) ---
            path_count = path_appearances.get(acc, 0)
            path_score = min(path_count * 6.0, 25.0)
            score += path_score
            if path_count > 0:
                why_factors.append(f"Appears along {path_count} reconstructed money-flow path(s) (+{int(path_score)} pts)")

            # --- C. Centrality Factor (max 15) ---
            role_hypo = roles.get(acc)
            betweenness = role_hypo.betweenness_centrality if role_hypo else 0.0
            cent_score = min(betweenness * 100.0, 15.0)
            score += cent_score
            if betweenness >= 0.05:
                why_factors.append(f"High network betweenness centrality ({betweenness:.3f}) indicating transit hub (+{int(cent_score)} pts)")

            # --- D. Volume Factor (max 15) ---
            acc_vol = (role_hypo.inflow_total_inr + role_hypo.outflow_total_inr) if role_hypo else 0.0
            vol_ratio = acc_vol / max_vol
            vol_score = min(vol_ratio * 15.0, 15.0)
            score += vol_score
            if acc_vol > 100000:
                why_factors.append(f"Substantial financial throughput ₹{acc_vol:,.2f} (+{int(vol_score)} pts)")

            # --- E. Role Operational Factor (max 10) ---
            role_val = role_hypo.probable_role if role_hypo else AccountRole.LEGITIMATE
            role_score_map = {
                AccountRole.MULE: 10.0,
                AccountRole.AGGREGATOR: 9.0,
                AccountRole.DISPERSER: 9.0,
                AccountRole.ORIGINATOR: 8.0,
                AccountRole.SINK: 8.0,
                AccountRole.LEGITIMATE: 0.0,
            }
            r_score = role_score_map.get(role_val, 2.0)
            score += r_score
            if role_val != AccountRole.LEGITIMATE:
                why_factors.append(f"Inferred probable role: {role_val.value} ({int(role_hypo.confidence*100)}% confidence) (+{int(r_score)} pts)")

            final_score = int(min(max(round(score), 0), 100))

            # Centrality rank label
            cent_label = "HIGH" if betweenness >= 0.1 else ("MEDIUM" if betweenness >= 0.02 else "LOW")

            item = InvestigationPriorityItem(
                account_id=acc,
                priority_score=final_score,
                probable_role=role_val,
                why_factors=why_factors if why_factors else ["Baseline activity, no suspicious indicators"],
                pattern_count=len(acc_patterns),
                path_appearances=path_count,
                total_volume_inr=round(acc_vol, 2),
                centrality_rank=cent_label,
            )
            results.append(item)

        # Sort descending by priority score
        return sorted(results, key=lambda x: x.priority_score, reverse=True)
