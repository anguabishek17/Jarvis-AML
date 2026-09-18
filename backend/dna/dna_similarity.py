"""
Behavioural Similarity Engine:
Compares a Money Trail DNA fingerprint against historical case reference typologies.
Calculates multi-dimensional similarity percentages: Retention, Velocity, Topology, Typology, and Role Sequence.
Explicitly frames findings as 'Behaviourally similar financial activity detected' for human analyst review.
"""
from typing import List
from backend.models.dna import MoneyTrailDNA, CaseSimilarityResult, HistoricalCase
from backend.data.historical_cases import get_historical_case_library


class BehaviouralSimilarityEngine:
    """
    Explainable multi-vector comparator:
    Total Similarity = 0.25 * Retention + 0.25 * Velocity + 0.20 * Topology + 0.15 * Typology + 0.15 * RoleSequence
    """

    def __init__(self, historical_cases: List[HistoricalCase] = None):
        self.cases = historical_cases if historical_cases is not None else get_historical_case_library()

    def find_similar_cases(self, current_dna: MoneyTrailDNA, top_k: int = 4) -> List[CaseSimilarityResult]:
        results: List[CaseSimilarityResult] = []

        for case in self.cases:
            # 1. Retention Similarity (0 to 100%)
            ret_diff = abs(current_dna.retention_score - case.retention_score)
            ret_sim = max(0.0, 100.0 - (ret_diff * 2.0))

            # 2. Velocity Similarity (0 to 100%)
            dwell_diff = abs(current_dna.avg_dwell_minutes - case.avg_dwell_minutes)
            vel_sim = max(0.0, 100.0 - (dwell_diff * 2.5))

            # 3. Topology Similarity (Hop Depth)
            hop_diff = abs(current_dna.hop_depth - case.hop_depth)
            topo_sim = max(0.0, 100.0 - (hop_diff * 25.0))

            # 4. Typology Matching (Typology code overlap)
            cur_tokens = set(current_dna.typology_code.replace("-", " ").split())
            case_tokens = set(case.typology_code.replace("-", " ").split())
            overlap = len(cur_tokens.intersection(case_tokens))
            union = len(cur_tokens.union(case_tokens))
            typo_sim = (overlap / union * 100.0) if union > 0 else 50.0

            # 5. Role Sequence Matching
            cur_roles = current_dna.role_sequence
            case_roles = case.role_sequence
            match_count = sum(1 for a, b in zip(cur_roles, case_roles) if a == b)
            max_len = max(len(cur_roles), len(case_roles), 1)
            role_sim = (match_count / max_len) * 100.0

            # Overall Weighted Similarity
            overall = (
                0.25 * ret_sim +
                0.25 * vel_sim +
                0.20 * topo_sim +
                0.15 * typo_sim +
                0.15 * role_sim
            )

            results.append(
                CaseSimilarityResult(
                    case_id=case.case_id,
                    case_title=case.case_title,
                    overall_similarity_pct=round(overall, 1),
                    typology_similarity_pct=round(typo_sim, 1),
                    retention_similarity_pct=round(ret_sim, 1),
                    velocity_similarity_pct=round(vel_sim, 1),
                    topology_similarity_pct=round(topo_sim, 1),
                    role_sequence_similarity_pct=round(role_sim, 1),
                    dna_signature=case.dna_signature,
                    known_typology_notes=case.typology_description,
                    investigative_leads=case.leads_and_playbook,
                )
            )

        # Sort descending by overall similarity
        return sorted(results, key=lambda x: x.overall_similarity_pct, reverse=True)[:top_k]
