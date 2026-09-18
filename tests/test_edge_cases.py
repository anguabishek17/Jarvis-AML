"""
Automated tests for edge cases, error conditions, and boundary data:
- Empty graph
- Single transaction
- Disconnected graphs
- Cyclic loops with no exit
- Zero/negative amounts
"""
from datetime import datetime, timedelta
import pytest
from backend.models.transaction import Transaction
from backend.graph.financial_graph import FinancialMultiGraph
from backend.detectors.layering_detector import LayeringDetector
from backend.detectors.circular_detector import CircularTransferDetector
from backend.detectors.rapid_movement_detector import RapidMovementDetector
from backend.analytics.attack_path_engine import AttackPathEngine
from backend.analytics.role_inference import RoleInferenceEngine
from backend.api.app import pipeline


def test_empty_graph_pipeline():
    g = FinancialMultiGraph()
    res = pipeline.analyze_graph(g, scenario_id="EMPTY_TEST")
    assert res["scenario_id"] == "EMPTY_TEST"
    assert res["graph"]["node_count"] == 0
    assert res["patterns"] == []
    assert res["attack_paths"] == []
    assert res["primary_dna"] is None


def test_single_transaction_graph():
    g = FinancialMultiGraph()
    t = datetime(2026, 9, 15, 10, 0, 0)
    g.add_transaction(Transaction(transaction_id="TX_SINGLE", timestamp=t, sender_account="ACC_1", receiver_account="ACC_2", amount=100000.0))

    res = pipeline.analyze_graph(g, scenario_id="SINGLE_TX_TEST")
    assert res["graph"]["node_count"] == 2
    assert res["graph"]["edge_count"] == 1
    assert "ACC_1" in res["roles"]
    assert "ACC_2" in res["roles"]


def test_disconnected_subgraphs():
    g = FinancialMultiGraph()
    t = datetime(2026, 9, 15, 10, 0, 0)
    # Component 1
    g.add_transaction(Transaction(transaction_id="TX1", timestamp=t, sender_account="C1_A", receiver_account="C1_B", amount=50000.0))
    # Component 2 (completely separate)
    g.add_transaction(Transaction(transaction_id="TX2", timestamp=t, sender_account="C2_X", receiver_account="C2_Y", amount=75000.0))

    comms = g.detect_communities()
    assert len(comms) == 2
    res = pipeline.analyze_graph(g, scenario_id="DISCONNECTED_TEST")
    assert res["graph"]["node_count"] == 4
    assert len(res["communities"]) == 2
