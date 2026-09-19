"""
Comprehensive test suite for JARVIS-AML Investigation Copilot.
Tests deterministic mathematical query resolution, grounded explainability,
evidence citation, and API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from backend.analytics.copilot_engine import CopilotEngine, InvestigationCopilotContext
from backend.analytics.simulation_engine import InvestigationSimulatorEngine
from backend.api.app import app, pipeline, get_case_investigation, get_case_graph


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def scenario_g_case():
    return get_case_investigation("SCENARIO_G")


@pytest.fixture
def scenario_g_graph():
    return get_case_graph("SCENARIO_G")


@pytest.fixture
def copilot_engine():
    return CopilotEngine()


def test_copilot_context_builder(scenario_g_case):
    ctx = InvestigationCopilotContext.from_case_payload(scenario_g_case)
    assert ctx.scenario_id == "SCENARIO_G"
    assert len(ctx.nodes) > 0
    assert len(ctx.edges) > 0
    assert len(ctx.attack_paths) > 0
    assert "ACC_GATEKEEPER_MULE" in ctx.roles


def test_copilot_longest_path_query(copilot_engine, scenario_g_case):
    ctx = InvestigationCopilotContext.from_case_payload(scenario_g_case)
    res = copilot_engine.answer_query(ctx, "What is the longest attack path?")

    assert "longest suspicious money trail" in res["answer"].lower() or "hops" in res["answer"].lower()
    assert len(res["paths"]) > 0
    assert len(res["actions"]) > 0
    assert any(a["type"] == "trace_path" for a in res["actions"])
    assert res["confidence"] == "HIGH"


def test_copilot_account_explanation_query(copilot_engine, scenario_g_case):
    ctx = InvestigationCopilotContext.from_case_payload(scenario_g_case)
    res = copilot_engine.answer_query(ctx, "Why is ACC_GATEKEEPER_MULE important?")

    assert "ACC_GATEKEEPER_MULE" in res["answer"]
    assert "ACC_GATEKEEPER_MULE" in res["entities"]
    assert len(res["why"]) > 0
    assert len(res["evidence"]) > 0
    assert any(a["type"] == "focus_node" for a in res["actions"])
    assert any(a["type"] == "open_simulator" for a in res["actions"])


def test_copilot_dna_query(copilot_engine, scenario_g_case):
    ctx = InvestigationCopilotContext.from_case_payload(scenario_g_case)
    res = copilot_engine.answer_query(ctx, "Explain the Money Trail DNA.")

    assert "DNA" in res["answer"] or "fingerprint" in res["answer"].lower()
    assert len(res["why"]) > 0
    assert any(a["type"] == "navigate_tab" for a in res["actions"])


def test_copilot_patterns_query(copilot_engine, scenario_g_case):
    ctx = InvestigationCopilotContext.from_case_payload(scenario_g_case)
    res = copilot_engine.answer_query(ctx, "What are the suspicious typologies detected?")

    assert "patterns" in res["answer"].lower() or "typolog" in res["answer"].lower()
    assert len(res["patterns"]) > 0
    assert len(res["evidence"]) > 0


def test_copilot_top_priority_query(copilot_engine, scenario_g_case):
    ctx = InvestigationCopilotContext.from_case_payload(scenario_g_case)
    res = copilot_engine.answer_query(ctx, "Who is the top priority entity?")

    assert "priority" in res["answer"].lower()
    assert len(res["entities"]) > 0
    assert len(res["actions"]) > 0


def test_copilot_volume_query(copilot_engine, scenario_g_case):
    ctx = InvestigationCopilotContext.from_case_payload(scenario_g_case)
    res = copilot_engine.answer_query(ctx, "What is the total transaction volume?")

    assert "₹" in res["answer"]
    assert "inflow" in res["answer"].lower() or "volume" in res["answer"].lower()


def test_copilot_summary_query(copilot_engine, scenario_g_case):
    ctx = InvestigationCopilotContext.from_case_payload(scenario_g_case)
    res = copilot_engine.answer_query(ctx, "Summarize this case for court evidence.")

    assert "investigation" in res["answer"].lower() or "dossier" in res["answer"].lower()
    assert len(res["why"]) > 0


def test_copilot_simulation_delta_query(copilot_engine, scenario_g_case, scenario_g_graph):
    # Run a simulation first
    sim_engine = InvestigationSimulatorEngine(pipeline)
    sim_result = sim_engine.simulate(
        original_graph=scenario_g_graph,
        original_analysis=scenario_g_case,
        target_type="account",
        target_id="ACC_GATEKEEPER_MULE",
        scenario_id="SCENARIO_G"
    )

    ctx = InvestigationCopilotContext.from_case_payload(scenario_g_case, latest_simulation=sim_result)
    res = copilot_engine.answer_query(ctx, "What would happen if ACC_GATEKEEPER_MULE is removed?")

    assert "ACC_GATEKEEPER_MULE" in res["answer"]
    assert "disrupt" in res["answer"].lower() or "broken" in res["answer"].lower() or "reduced" in res["answer"].lower()
    assert any(a["type"] == "focus_simulation" or a["type"] == "open_simulator" for a in res["actions"])


def test_copilot_unsupported_query_grounding(copilot_engine, scenario_g_case):
    ctx = InvestigationCopilotContext.from_case_payload(scenario_g_case)
    # Ask something completely out of AML scope / not in graph
    res = copilot_engine.answer_query(ctx, "What is the weather forecast for London tomorrow?")

    assert "I don't have sufficient evidence in the current investigation data" in res["answer"]
    assert res["confidence"] == "LOW"


def test_copilot_api_endpoints(client):
    # Test GET context
    ctx_res = client.get("/api/copilot/context/SCENARIO_G")
    assert ctx_res.status_code == 200
    ctx_data = ctx_res.json()
    assert ctx_data["scenario_id"] == "SCENARIO_G"
    assert "node_count" in ctx_data

    # Test POST query
    q_res = client.post("/api/copilot/query", json={
        "scenario_id": "SCENARIO_G",
        "question": "What is the longest attack path?"
    })
    assert q_res.status_code == 200
    q_data = q_res.json()
    assert "answer" in q_data
    assert "actions" in q_data
    assert "confidence" in q_data
    assert len(q_data["actions"]) > 0


def test_copilot_custom_case_account_query_regression(client):
    """
    Regression Test: Given a custom case created from benchmark CSV containing ACC_GATEKEEPER_MULE_1,
    Copilot must resolve 'Why is ACC_GATEKEEPER_MULE important?' to the actual active node,
    and return evidence-grounded findings rather than reporting zero recorded transactions.
    """
    from backend.ingestion.sample_generator import get_sample_csv_text
    
    # 1. Create custom case via /api/investigate/custom
    csv_payload = get_sample_csv_text()
    resp = client.post("/api/investigate/custom", json={"csv_text": csv_payload, "dataset_name": "Regression Test Case"})
    assert resp.status_code == 200
    custom_case = resp.json()
    case_id = custom_case["scenario_id"]

    # 2. Query Copilot context
    ctx_resp = client.get(f"/api/copilot/context/{case_id}")
    assert ctx_resp.status_code == 200
    ctx_json = ctx_resp.json()
    assert ctx_json["account_count"] == 16

    # 3. Query Copilot for ACC_GATEKEEPER_MULE (both with and without suffix)
    q_resp = client.post("/api/copilot/query", json={
        "scenario_id": case_id,
        "question": "Why is ACC_GATEKEEPER_MULE important?"
    })
    assert q_resp.status_code == 200
    q_res = q_resp.json()

    # Copilot must NOT report lack of transactions
    assert "does not participate in any recorded transactions" not in q_res["answer"]
    assert "don't have sufficient evidence" not in q_res["answer"]
    assert len(q_res["why"]) > 0
    assert len(q_res["evidence"]) > 0
    assert len(q_res["actions"]) > 0

    # 4. Query genuinely unknown account and verify fallback is retained
    unknown_resp = client.post("/api/copilot/query", json={
        "scenario_id": case_id,
        "question": "Why is ACC_NONEXISTENT_ACCOUNT important?"
    })
    assert unknown_resp.status_code == 200
    unk_res = unknown_resp.json()
    assert "I don't have sufficient evidence in the current investigation data for account ACC_NONEXISTENT_ACCOUNT" in unk_res["answer"]
    assert "does not participate in any recorded transactions" in unk_res["why"][0]

