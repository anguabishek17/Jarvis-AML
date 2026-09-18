"""
Automated tests for MoneyTrailDNAEngine and BehaviouralSimilarityEngine:
- Deterministic DNA generation
- Gene encoding accuracy
- SHA-256 evidence integrity hashing
- Stage-by-stage evolution
- Behavioural similarity matching against historical case library
"""
from backend.graph.financial_graph import FinancialMultiGraph
from backend.detectors.layering_detector import LayeringDetector
from backend.detectors.circular_detector import CircularTransferDetector
from backend.detectors.rapid_movement_detector import RapidMovementDetector
from backend.detectors.fan_patterns_detector import FanPatternsDetector
from backend.analytics.attack_path_engine import AttackPathEngine
from backend.analytics.role_inference import RoleInferenceEngine
from backend.dna.dna_engine import MoneyTrailDNAEngine
from backend.dna.dna_similarity import BehaviouralSimilarityEngine
from backend.data.scenarios import create_scenario_g_primary


def test_dna_generation_and_determinism():
    meta, accounts, txs = create_scenario_g_primary()
    g = FinancialMultiGraph()
    g.load_transactions(txs, accounts)

    # Detect patterns
    findings = []
    findings.extend(LayeringDetector().detect(g))
    findings.extend(CircularTransferDetector().detect(g))
    findings.extend(RapidMovementDetector().detect(g))
    findings.extend(FanPatternsDetector().detect_all(g))

    roles = RoleInferenceEngine().infer_roles(g, findings)
    paths = AttackPathEngine().reconstruct_paths(g)

    assert len(paths) >= 1
    top_path = paths[0]

    engine = MoneyTrailDNAEngine()
    dna1 = engine.generate_dna_for_path(top_path, g, roles, findings)
    dna2 = engine.generate_dna_for_path(top_path, g, roles, findings)

    # Check Determinism
    assert dna1.signature == dna2.signature
    assert dna1.evidence_payload_sha256 == dna2.evidence_payload_sha256
    assert dna1.signature.startswith("DNA-")
    assert "RET" in dna1.signature
    assert "VEL" in dna1.signature
    assert "H" in dna1.signature

    # Check Genes
    assert len(dna1.genes) == 6
    for gene in dna1.genes:
        assert len(gene.why_explanation) > 10
        assert len(gene.supporting_transaction_ids) > 0

    # Check Evolution
    assert len(dna1.evolution_stages) >= 3


def test_behavioural_similarity_matching():
    meta, accounts, txs = create_scenario_g_primary()
    g = FinancialMultiGraph()
    g.load_transactions(txs, accounts)

    findings = RapidMovementDetector().detect(g) + LayeringDetector().detect(g)
    roles = RoleInferenceEngine().infer_roles(g, findings)
    paths = AttackPathEngine().reconstruct_paths(g)

    dna = MoneyTrailDNAEngine().generate_dna_for_path(paths[0], g, roles, findings)

    sim_engine = BehaviouralSimilarityEngine()
    results = sim_engine.find_similar_cases(dna)

    assert len(results) > 0
    top_match = results[0]
    assert top_match.overall_similarity_pct >= 60.0
    assert top_match.case_id in ["CASE-007", "CASE-014", "CASE-021", "CASE-035"]
    assert len(top_match.investigative_leads) > 0
