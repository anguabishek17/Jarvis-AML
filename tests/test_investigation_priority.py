"""
Automated tests for InvestigationPriorityEngine:
- Score ranges (0-100)
- Triage ranking order
- Reason factors explainability
"""
from backend.graph.financial_graph import FinancialMultiGraph
from backend.detectors.layering_detector import LayeringDetector
from backend.detectors.circular_detector import CircularTransferDetector
from backend.detectors.rapid_movement_detector import RapidMovementDetector
from backend.detectors.fan_patterns_detector import FanPatternsDetector
from backend.analytics.attack_path_engine import AttackPathEngine
from backend.analytics.role_inference import RoleInferenceEngine
from backend.analytics.priority_engine import InvestigationPriorityEngine
from backend.data.scenarios import create_scenario_g_primary


def test_investigation_priority_scoring_scenario_g():
    meta, accounts, txs = create_scenario_g_primary()
    g = FinancialMultiGraph()
    g.load_transactions(txs, accounts)

    findings = []
    findings.extend(LayeringDetector().detect(g))
    findings.extend(CircularTransferDetector().detect(g))
    findings.extend(RapidMovementDetector().detect(g))
    findings.extend(FanPatternsDetector().detect_all(g))

    roles = RoleInferenceEngine().infer_roles(g, findings)
    paths = AttackPathEngine().reconstruct_paths(g)

    engine = InvestigationPriorityEngine()
    priority_list = engine.compute_priority_rankings(g, roles, findings, paths)

    assert len(priority_list) == len(accounts)
    
    # Priority scores must be strictly between 0 and 100
    for item in priority_list:
        assert 0 <= item.priority_score <= 100
        assert len(item.why_factors) > 0

    # Top scored accounts should be suspicious intermediaries/hubs
    top_account_ids = [item.account_id for item in priority_list[:4]]
    assert any(acc in top_account_ids for acc in ["ACC_GATEKEEPER_MULE", "ACC_DISPERSER_HUB", "ACC_MULE_TRANSIT_X1", "ACC_AGGREGATOR_X"])
