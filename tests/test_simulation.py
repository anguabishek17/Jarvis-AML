"""
Unit and integration tests for JARVIS-AML Investigation Simulator Engine (What-If Analysis).
"""
import pytest
from backend.analytics.simulation_engine import InvestigationSimulatorEngine
from backend.api.app import pipeline, get_case_investigation, get_case_graph, app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_simulation_engine_account_removal_scenario_g():
    graph = get_case_graph("SCENARIO_G")
    orig_analysis = get_case_investigation("SCENARIO_G")
    sim_engine = InvestigationSimulatorEngine(pipeline)

    # Simulate removing gatekeeper mule
    result = sim_engine.simulate(
        original_graph=graph,
        original_analysis=orig_analysis,
        target_type="account",
        target_id="ACC_GATEKEEPER_MULE",
        scenario_id="SCENARIO_G",
    )

    assert result["scenario_id"] == "SCENARIO_G"
    assert result["target"]["target_id"] == "ACC_GATEKEEPER_MULE"
    assert result["target"]["target_type"] == "account"

    comp = result["comparison"]
    # Verify before vs after metrics are real numbers
    assert comp["attack_paths"]["before"] >= 1
    assert comp["transactions_count"]["before"] > comp["transactions_count"]["after"]
    assert comp["total_volume_inr"]["before"] > comp["total_volume_inr"]["after"]
    assert comp["case_priority_score"]["before"] >= comp["case_priority_score"]["after"]

    # Verify path impact
    paths = result["path_impact"]
    assert len(paths) >= 1
    broken_paths = [p for p in paths if p["status"] == "BROKEN"]
    assert len(broken_paths) >= 1
    assert "ACC_GATEKEEPER_MULE" in broken_paths[0]["reason"]

    # Verify pattern impact
    pat_impact = result["pattern_impact"]
    assert "removed" in pat_impact
    assert "persisted" in pat_impact

    # Verify DNA impact
    dna_impact = result["dna_impact"]
    assert "signature_before" in dna_impact
    assert "signature_after" in dna_impact
    assert "genes" in dna_impact
    assert "typology" in dna_impact["genes"]
    assert "retention" in dna_impact["genes"]

    # Verify Why This Matters narrative
    assert len(result["why_this_matters"]) > 20
    assert "ACC_GATEKEEPER_MULE" in result["why_this_matters"]


def test_simulation_engine_transaction_removal():
    graph = get_case_graph("SCENARIO_G")
    orig_analysis = get_case_investigation("SCENARIO_G")
    sim_engine = InvestigationSimulatorEngine(pipeline)

    txs = graph.get_all_transactions()
    assert len(txs) > 0
    target_tx = txs[0].transaction_id

    result = sim_engine.simulate(
        original_graph=graph,
        original_analysis=orig_analysis,
        target_type="transaction",
        target_id=target_tx,
        scenario_id="SCENARIO_G",
    )

    assert result["target"]["target_id"] == target_tx
    assert result["comparison"]["transactions_count"]["after"] == result["comparison"]["transactions_count"]["before"] - 1


def test_simulation_nonexistent_target_raises_error():
    graph = get_case_graph("SCENARIO_G")
    orig_analysis = get_case_investigation("SCENARIO_G")
    sim_engine = InvestigationSimulatorEngine(pipeline)

    with pytest.raises(ValueError, match="not found"):
        sim_engine.simulate(
            original_graph=graph,
            original_analysis=orig_analysis,
            target_type="account",
            target_id="ACC_NONEXISTENT_999",
            scenario_id="SCENARIO_G",
        )


def test_simulation_api_get_targets():
    res = client.get("/api/simulate/SCENARIO_G/targets")
    assert res.status_code == 200
    data = res.json()
    assert data["scenario_id"] == "SCENARIO_G"
    assert len(data["accounts"]) >= 5
    assert len(data["transactions"]) >= 5

    # Check structure of account target
    first_acc = data["accounts"][0]
    assert "account_id" in first_acc
    assert "probable_role" in first_acc
    assert "inflow_total_inr" in first_acc


def test_simulation_api_post_simulate():
    payload = {
        "target_type": "account",
        "target_id": "ACC_GATEKEEPER_MULE",
    }
    res = client.post("/api/simulate/SCENARIO_G", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["scenario_id"] == "SCENARIO_G"
    assert data["target"]["target_id"] == "ACC_GATEKEEPER_MULE"
    assert "comparison" in data
    assert "path_impact" in data
    assert "pattern_impact" in data
    assert "dna_impact" in data
    assert "simulated_graph" in data
    assert "diff_highlights" in data


def test_simulation_api_invalid_target_404():
    payload = {
        "target_type": "account",
        "target_id": "ACC_DOES_NOT_EXIST",
    }
    res = client.post("/api/simulate/SCENARIO_G", json=payload)
    assert res.status_code == 404
