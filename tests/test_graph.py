"""
Automated unit tests for FinancialMultiGraph:
- Node/edge additions
- Multigraph parallel edge preservation
- Metric calculations (in/out degree, forwarding ratio, dwell time)
- Centrality measures
- Upstream and downstream bounded BFS
- 2-hop neighborhood extraction
- Community detection
"""
from datetime import datetime, timedelta
import pytest
from backend.models.transaction import Transaction, Account, PaymentChannel, TransactionType
from backend.graph.financial_graph import FinancialMultiGraph


def test_graph_initialization_and_empty():
    g = FinancialMultiGraph()
    assert g.get_node_count() == 0
    assert g.get_edge_count() == 0
    assert g.compute_centrality_metrics() == {}
    assert g.detect_communities() == []


def test_multigraph_parallel_edges():
    g = FinancialMultiGraph()
    t1 = datetime(2026, 9, 15, 10, 0, 0)
    tx1 = Transaction(transaction_id="TX01", timestamp=t1, sender_account="ACC_A", receiver_account="ACC_B", amount=10000.0)
    tx2 = Transaction(transaction_id="TX02", timestamp=t1 + timedelta(minutes=5), sender_account="ACC_A", receiver_account="ACC_B", amount=20000.0)

    g.add_transaction(tx1)
    g.add_transaction(tx2)

    assert g.get_node_count() == 2
    assert g.get_edge_count() == 2
    metrics_a = g.get_account_metrics("ACC_A")
    assert metrics_a["out_degree"] == 2
    assert metrics_a["outflow_total"] == 30000.0


def test_upstream_and_downstream_tracing():
    g = FinancialMultiGraph()
    t = datetime(2026, 9, 15, 10, 0, 0)
    g.add_transaction(Transaction(transaction_id="T1", timestamp=t, sender_account="SRC", receiver_account="MID", amount=50000.0))
    g.add_transaction(Transaction(transaction_id="T2", timestamp=t + timedelta(minutes=10), sender_account="MID", receiver_account="DST", amount=49000.0))

    # Upstream from DST
    up = g.trace_upstream("DST", max_depth=2)
    assert "MID" in up["nodes"]
    assert "SRC" in up["nodes"]
    assert len(up["edges"]) == 2

    # Downstream from SRC
    down = g.trace_downstream("SRC", max_depth=2)
    assert "MID" in down["nodes"]
    assert "DST" in down["nodes"]
    assert len(down["edges"]) == 2


def test_2hop_neighborhood():
    g = FinancialMultiGraph()
    t = datetime(2026, 9, 15, 10, 0, 0)
    g.add_transaction(Transaction(transaction_id="T1", timestamp=t, sender_account="A", receiver_account="B", amount=1000.0))
    g.add_transaction(Transaction(transaction_id="T2", timestamp=t + timedelta(minutes=5), sender_account="B", receiver_account="C", amount=900.0))

    n2 = g.extract_2hop_neighborhood("B")
    assert set(n2["nodes"]) == {"A", "B", "C"}
    assert len(n2["edges"]) == 2


def test_centrality_and_communities():
    g = FinancialMultiGraph()
    t = datetime(2026, 9, 15, 10, 0, 0)
    g.add_transaction(Transaction(transaction_id="T1", timestamp=t, sender_account="A", receiver_account="HUB", amount=10000.0))
    g.add_transaction(Transaction(transaction_id="T2", timestamp=t + timedelta(minutes=5), sender_account="HUB", receiver_account="B", amount=9000.0))
    g.add_transaction(Transaction(transaction_id="T3", timestamp=t + timedelta(minutes=10), sender_account="HUB", receiver_account="C", amount=9000.0))

    cent = g.compute_centrality_metrics()
    assert cent["HUB"]["betweenness"] > 0.0

    comms = g.detect_communities()
    assert len(comms) == 1
    assert set(comms[0]["members"]) == {"A", "HUB", "B", "C"}
