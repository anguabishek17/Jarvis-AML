"""
Automated tests for FastAPI REST API endpoints.
"""
import pytest
from starlette.testclient import TestClient
from backend.api.app import app

client = TestClient(app)


def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ONLINE"


def test_api_list_scenarios():
    res = client.get("/api/scenarios")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 7
    ids = [s["scenario_id"] for s in data]
    assert "SCENARIO_G" in ids
    assert "SCENARIO_A" in ids


def test_api_get_case_scenario_g():
    res = client.get("/api/cases/SCENARIO_G")
    assert res.status_code == 200
    data = res.json()
    assert data["scenario_id"] == "SCENARIO_G"
    assert "graph" in data
    assert "patterns" in data
    assert len(data["patterns"]) >= 3
    assert "attack_paths" in data
    assert len(data["attack_paths"]) >= 1
    assert "roles" in data
    assert "temporal_stages" in data
    assert "priority_rankings" in data
    assert "primary_dna" in data
    assert "similar_cases" in data
    assert "narrative_brief" in data
    assert "chronological_storyline" in data


def test_api_trace_endpoint():
    res = client.get("/api/trace/SCENARIO_G/ACC_GATEKEEPER_MULE")
    assert res.status_code == 200
    data = res.json()
    assert data["focus_account"] == "ACC_GATEKEEPER_MULE"
    assert "upstream" in data
    assert "downstream" in data
    assert "neighborhood_2hop" in data


def test_api_dna_evidence_endpoint():
    # Fetch case to get path ID
    res_case = client.get("/api/cases/SCENARIO_G")
    case_data = res_case.json()
    path_id = case_data["attack_paths"][0]["path_id"]

    res_ev = client.get(f"/api/dna/SCENARIO_G/{path_id}/evidence")
    assert res_ev.status_code == 200
    ev_data = res_ev.json()
    assert "sha256_forensic_integrity_seal" in ev_data
    assert len(ev_data["sha256_forensic_integrity_seal"]) == 64
    assert len(ev_data["genes"]) == 6
