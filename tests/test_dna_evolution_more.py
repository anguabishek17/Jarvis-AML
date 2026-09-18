"""
Additional tests for DNA Evolution, Custom Ingestion, and Multigraph Trace Boundary conditions.
"""
from datetime import datetime, timedelta
import pytest
from backend.models.transaction import Transaction, PaymentChannel
from backend.graph.financial_graph import FinancialMultiGraph
from backend.detectors.layering_detector import LayeringDetector
from backend.detectors.rapid_movement_detector import RapidMovementDetector
from backend.analytics.attack_path_engine import AttackPathEngine
from backend.analytics.role_inference import RoleInferenceEngine
from backend.dna.dna_engine import MoneyTrailDNAEngine
from backend.api.app import pipeline


def test_dna_evolution_progression():
    g = FinancialMultiGraph()
    t = datetime(2026, 9, 15, 10, 0, 0)
    # 4 hops
    txs = [
        Transaction(transaction_id="TX_E1", timestamp=t, sender_account="A", receiver_account="B", amount=100000.0),
        Transaction(transaction_id="TX_E2", timestamp=t + timedelta(minutes=5), sender_account="B", receiver_account="C", amount=98000.0),
        Transaction(transaction_id="TX_E3", timestamp=t + timedelta(minutes=10), sender_account="C", receiver_account="D", amount=96000.0),
        Transaction(transaction_id="TX_E4", timestamp=t + timedelta(minutes=15), sender_account="D", receiver_account="E", amount=95000.0),
    ]
    g.load_transactions(txs)
    findings = LayeringDetector().detect(g) + RapidMovementDetector().detect(g)
    roles = RoleInferenceEngine().infer_roles(g, findings)
    paths = AttackPathEngine().reconstruct_paths(g)

    assert len(paths) >= 1
    dna = MoneyTrailDNAEngine().generate_dna_for_path(paths[0], g, roles, findings)

    assert len(dna.evolution_stages) == 4
    for idx, stage in enumerate(dna.evolution_stages, 1):
        assert stage.stage_index == idx
        assert len(stage.active_dna_signature) > 0


def test_custom_dataset_ingestion():
    t = datetime(2026, 9, 15, 10, 0, 0)
    txs = [
        Transaction(transaction_id="TX_C1", timestamp=t, sender_account="X", receiver_account="Y", amount=500000.0),
        Transaction(transaction_id="TX_C2", timestamp=t + timedelta(minutes=10), sender_account="Y", receiver_account="Z", amount=490000.0),
    ]
    g = FinancialMultiGraph()
    g.load_transactions(txs)
    res = pipeline.analyze_graph(g, scenario_id="CUSTOM_TEST")

    assert res["scenario_id"] == "CUSTOM_TEST"
    assert res["graph"]["node_count"] == 3
    assert res["graph"]["edge_count"] == 2


def test_zero_amount_validation():
    with pytest.raises(Exception):
        Transaction(transaction_id="TX_ZERO", timestamp=datetime.utcnow(), sender_account="A", receiver_account="B", amount=0.0)


def test_trace_depth_bounds():
    g = FinancialMultiGraph()
    t = datetime(2026, 9, 15, 10, 0, 0)
    for i in range(10):
        g.add_transaction(Transaction(
            transaction_id=f"TX_SEQ_{i}",
            timestamp=t + timedelta(minutes=i*2),
            sender_account=f"N_{i}",
            receiver_account=f"N_{i+1}",
            amount=100000.0 - (i * 1000),
        ))

    # Test depth bounding at max_depth=2
    down = g.trace_downstream("N_0", max_depth=2)
    assert len(down["nodes"]) <= 4
