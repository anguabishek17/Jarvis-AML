"""
Investigation Storyline & Narrative Engine:
Transforms structured evidence, attack paths, role hypotheses, and DNA fingerprints
into clear, concise, investigator-grade case briefings and chronological storylines.
Maintains strict evidentiary neutrality (no unsupported criminality claims).
"""
from typing import List, Dict, Any, Optional
from backend.models.findings import AttackPath, AccountRoleHypothesis, PatternFinding, SuspiciousCommunity
from backend.models.dna import MoneyTrailDNA, CaseSimilarityResult


class StorylineEngine:
    """
    Deterministic template-based narrative generator with an extensible abstraction interface.
    """

    def generate_executive_summary(
        self,
        scenario_id: str,
        graph_data: Dict[str, Any],
        findings: List[PatternFinding],
        attack_paths: List[AttackPath],
        dna: Optional[MoneyTrailDNA],
        similar_cases: List[CaseSimilarityResult],
    ) -> Dict[str, Any]:
        total_vol = sum(edge.get("amount", 0.0) for edge in graph_data.get("edges", []))
        node_count = graph_data.get("node_count", 0)
        edge_count = graph_data.get("edge_count", 0)
        pat_types = list(set(f.pattern_type.value for f in findings))

        primary_path = attack_paths[0] if attack_paths else None
        top_similar = similar_cases[0] if similar_cases else None

        # Executive Briefing
        summary_text = (
            f"JARVIS-AML investigation completed for {scenario_id}. "
            f"The network encompasses {node_count} monitored accounts and {edge_count} transactions "
            f"totaling ₹{total_vol:,.2f}. "
            f"Analysis detected {len(findings)} suspicious pattern clusters ({', '.join(pat_types)}). "
        )

        if primary_path:
            summary_text += (
                f"The highest-priority money trail spans {primary_path.hop_count} hops from {primary_path.source_account} "
                f"to {primary_path.destination_account}, transferring ₹{primary_path.total_inflow_inr:,.2f} "
                f"with {primary_path.retention_percentage}% retention over {primary_path.elapsed_minutes:.1f} minutes. "
            )

        if dna:
            summary_text += f"The generated Money Trail DNA fingerprint is '{dna.signature}'. "

        if top_similar:
            summary_text += (
                f"Behavioural similarity analysis identifies an {top_similar.overall_similarity_pct}% alignment "
                f"with historical reference '{top_similar.case_title}' ({top_similar.case_id})."
            )

        # Actionable Leads
        investigative_leads = []
        if primary_path:
            investigative_leads.append(f"Issue priority inquiry regarding originator account {primary_path.source_account} and initial source of funds.")
            if primary_path.intermediate_accounts:
                investigative_leads.append(f"Request immediate transactional audit for transit/mule accounts: {', '.join(primary_path.intermediate_accounts)}.")
            investigative_leads.append(f"Inspect beneficiary account {primary_path.destination_account} for subsequent cash withdrawals or overseas RTGS transfers.")

        if top_similar and top_similar.investigative_leads:
            investigative_leads.extend(top_similar.investigative_leads)

        return {
            "title": f"Investigation Intelligence Briefing: {scenario_id}",
            "executive_summary": summary_text,
            "key_metrics": {
                "total_monitored_accounts": node_count,
                "total_transactions": edge_count,
                "total_volume_inr": round(total_vol, 2),
                "patterns_detected_count": len(findings),
                "reconstructed_paths_count": len(attack_paths),
                "dna_fingerprint": dna.signature if dna else "N/A",
                "top_historical_match": f"{top_similar.case_id} ({top_similar.overall_similarity_pct}%)" if top_similar else "N/A",
            },
            "investigative_leads": list(dict.fromkeys(investigative_leads)),
        }

    def generate_chronological_storyline(
        self,
        attack_paths: List[AttackPath],
        graph_data: Dict[str, Any],
        roles: Dict[str, AccountRoleHypothesis],
    ) -> List[Dict[str, Any]]:
        edges = sorted(graph_data.get("edges", []), key=lambda x: x.get("timestamp", ""))
        storyline_steps = []

        for idx, edge in enumerate(edges, 1):
            src = edge.get("source")
            tgt = edge.get("target")
            amt = edge.get("amount", 0.0)
            channel = edge.get("channel", "IMPS")
            ts = edge.get("timestamp", "")

            src_role = roles.get(src).probable_role.value if src in roles else "ENTITY"
            tgt_role = roles.get(tgt).probable_role.value if tgt in roles else "ENTITY"

            desc = f"Funds of ₹{amt:,.2f} moved via {channel} from {src} ({src_role}) to {tgt} ({tgt_role})."

            storyline_steps.append({
                "step_index": idx,
                "timestamp": ts,
                "source_account": src,
                "target_account": tgt,
                "amount_inr": amt,
                "channel": channel,
                "narrative": desc,
            })

        return storyline_steps
