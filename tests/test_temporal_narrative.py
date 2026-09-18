"""
Automated tests for Temporal Intelligence and Storyline Engine:
- Stage lifecycle transitions (INJECTION -> DISPERSION -> LAYERING -> CONVERGENCE -> SINK)
- Chronological narrative generation
- Executive briefing metrics
"""
from backend.graph.financial_graph import FinancialMultiGraph
from backend.detectors.layering_detector import LayeringDetector
from backend.detectors.rapid_movement_detector import RapidMovementDetector
from backend.detectors.fan_patterns_detector import FanPatternsDetector
from backend.analytics.attack_path_engine import AttackPathEngine
from backend.analytics.role_inference import RoleInferenceEngine
from backend.analytics.temporal_engine import TemporalEngine
from backend.narrative.storyline_engine import StorylineEngine
from backend.dna.dna_engine import MoneyTrailDNAEngine
from backend.data.scenarios import create_scenario_g_primary


def test_temporal_stages_scenario_g():
    meta, accounts, txs = create_scenario_g_primary()
    g = FinancialMultiGraph()
    g.load_transactions(txs, accounts)

    findings = RapidMovementDetector().detect(g) + LayeringDetector().detect(g) + FanPatternsDetector().detect_all(g)
    roles = RoleInferenceEngine().infer_roles(g, findings)

    t_engine = TemporalEngine()
    stages = t_engine.analyze_stages(g, roles, findings)

    assert len(stages) >= 3
    stage_names = [s["stage_name"] for s in stages]
    assert "INJECTION" in stage_names
    assert "DISPERSION" in stage_names or "LAYERING" in stage_names
    
    for s in stages:
        assert s["volume_inr"] > 0
        assert len(s["accounts_active"]) >= 2
        assert len(s["transaction_ids"]) >= 1


def test_storyline_and_executive_summary():
    meta, accounts, txs = create_scenario_g_primary()
    g = FinancialMultiGraph()
    g.load_transactions(txs, accounts)

    findings = RapidMovementDetector().detect(g) + LayeringDetector().detect(g)
    roles = RoleInferenceEngine().infer_roles(g, findings)
    paths = AttackPathEngine().reconstruct_paths(g)
    dna = MoneyTrailDNAEngine().generate_dna_for_path(paths[0], g, roles, findings)

    story_engine = StorylineEngine()
    briefing = story_engine.generate_executive_summary(
        scenario_id="SCENARIO_G",
        graph_data=g.to_dict(),
        findings=findings,
        attack_paths=paths,
        dna=dna,
        similar_cases=[],
    )

    assert "SCENARIO_G" in briefing["title"]
    assert len(briefing["executive_summary"]) > 50
    assert briefing["key_metrics"]["total_transactions"] == 14
    assert len(briefing["investigative_leads"]) >= 1

    chronology = story_engine.generate_chronological_storyline(paths, g.to_dict(), roles)
    assert len(chronology) == 14
    assert chronology[0]["source_account"] == "ACC_ORIGINATOR_A"
