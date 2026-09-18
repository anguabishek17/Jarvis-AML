"""
Automated tests for AttackPathEngine:
- Path extraction accuracy
- Retention calculations
- Intermediate account ordering
- Risk ranking
"""
from backend.graph.financial_graph import FinancialMultiGraph
from backend.analytics.attack_path_engine import AttackPathEngine
from backend.data.scenarios import create_scenario_b_layering, create_scenario_g_primary


def test_attack_path_extraction_scenario_b():
    meta, accounts, txs = create_scenario_b_layering()
    g = FinancialMultiGraph()
    g.load_transactions(txs, accounts)

    engine = AttackPathEngine(min_hops=2)
    paths = engine.reconstruct_paths(g)

    assert len(paths) >= 1
    p = paths[0]
    assert p.source_account == "ACC_ORIGINATOR_B"
    assert p.destination_account == "ACC_SINK_B"
    assert p.hop_count == 4
    assert p.retention_percentage == 90.0
    assert len(p.intermediate_accounts) == 3


def test_attack_path_extraction_scenario_g():
    meta, accounts, txs = create_scenario_g_primary()
    g = FinancialMultiGraph()
    g.load_transactions(txs, accounts)

    engine = AttackPathEngine(min_hops=2)
    paths = engine.reconstruct_paths(g)

    assert len(paths) >= 1
    top_path = paths[0]
    assert top_path.source_account == "ACC_ORIGINATOR_A"
    assert top_path.destination_account == "ACC_SINK_DEST"
    assert top_path.hop_count >= 4
    assert top_path.retention_percentage > 85.0
