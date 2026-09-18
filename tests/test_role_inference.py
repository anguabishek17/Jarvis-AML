"""
Automated tests for RoleInferenceEngine:
- Heuristic role classification
- Confidence scores
- Evidence signals
"""
from backend.graph.financial_graph import FinancialMultiGraph
from backend.analytics.role_inference import RoleInferenceEngine
from backend.models.findings import AccountRole
from backend.data.scenarios import create_scenario_g_primary


def test_role_inference_scenario_g():
    meta, accounts, txs = create_scenario_g_primary()
    g = FinancialMultiGraph()
    g.load_transactions(txs, accounts)

    engine = RoleInferenceEngine()
    roles = engine.infer_roles(g)

    assert "ACC_ORIGINATOR_A" in roles
    assert roles["ACC_ORIGINATOR_A"].probable_role == AccountRole.ORIGINATOR
    assert roles["ACC_ORIGINATOR_A"].confidence >= 0.85

    assert "ACC_GATEKEEPER_MULE" in roles
    assert roles["ACC_GATEKEEPER_MULE"].probable_role == AccountRole.MULE

    assert "ACC_DISPERSER_HUB" in roles
    assert roles["ACC_DISPERSER_HUB"].probable_role == AccountRole.DISPERSER

    assert "ACC_AGGREGATOR_X" in roles
    assert roles["ACC_AGGREGATOR_X"].probable_role == AccountRole.AGGREGATOR

    assert "ACC_SINK_DEST" in roles
    assert roles["ACC_SINK_DEST"].probable_role == AccountRole.SINK
