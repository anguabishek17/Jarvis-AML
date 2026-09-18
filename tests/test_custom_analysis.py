"""
Comprehensive Automated Tests for Custom Transaction Ingestion & Investigation Engine.
Tests validation, normalization, graph construction, AML detectors, attack path reconstruction,
Money Trail DNA generation, similarity matching, no-suspicion handling, and scenario regression.
"""
from datetime import datetime, timedelta
import io
import pytest
from starlette.testclient import TestClient

from backend.api.app import app, CUSTOM_CASES_REGISTRY
from backend.ingestion.validator import TransactionValidator
from backend.ingestion.normalizer import map_column_headers, parse_flexible_amount, parse_flexible_timestamp
from backend.ingestion.sample_generator import get_sample_csv_text
from backend.graph.financial_graph import FinancialMultiGraph
from backend.detectors.layering_detector import LayeringDetector
from backend.detectors.circular_detector import CircularTransferDetector
from backend.detectors.rapid_movement_detector import RapidMovementDetector
from backend.detectors.fan_patterns_detector import FanPatternsDetector
from backend.analytics.attack_path_engine import AttackPathEngine
from backend.analytics.role_inference import RoleInferenceEngine
from backend.dna.dna_engine import MoneyTrailDNAEngine
from backend.dna.dna_similarity import BehaviouralSimilarityEngine

client = TestClient(app)
validator = TransactionValidator()


# 1. Test CSV Upload via API
def test_custom_csv_upload():
    csv_data = get_sample_csv_text()
    response = client.post(
        "/api/investigate/custom",
        files={"file": ("test_upload.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "custom"
    assert data["case_id"].startswith("CUSTOM-")
    assert len(data["attack_paths"]) >= 1
    assert data["primary_dna"] is not None
    assert "signature" in data["primary_dna"]
    assert len(data["patterns"]) >= 3


# 2. Test JSON Input via API
def test_custom_json_input():
    payload = {
        "transactions": [
            {"txn_id": "T01", "datetime": "2026-09-18 10:00:00", "source": "ACC_X1", "destination": "ACC_X2", "amt": 500000, "channel": "IMPS"},
            {"txn_id": "T02", "datetime": "2026-09-18 10:07:00", "source": "ACC_X2", "destination": "ACC_X3", "amt": 490000, "channel": "IMPS"},
            {"txn_id": "T03", "datetime": "2026-09-18 10:15:00", "source": "ACC_X3", "destination": "ACC_X4", "amt": 480000, "channel": "IMPS"},
        ]
    }
    response = client.post("/api/investigate/custom", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["graph"]["node_count"] == 4
    assert data["graph"]["edge_count"] == 3


# 3. Test Required Column Validation
def test_required_column_validation():
    bad_csv = "id,timestamp,amount\n1,2026-09-18,5000"
    report, txs = validator.validate_csv_text(bad_csv)
    assert not report.is_acceptable_for_analysis
    assert len(report.errors) > 0
    assert any("sender" in e.lower() or "receiver" in e.lower() for e in report.errors)


# 4. Test Invalid Timestamp
def test_invalid_timestamp():
    bad_time_csv = "transaction_id,timestamp,sender,receiver,amount\nTX01,INVALID_DATE_XYZ,A,B,100000"
    report, txs = validator.validate_csv_text(bad_time_csv)
    assert report.invalid_rows == 1
    assert len(report.errors) >= 1
    assert "Invalid timestamp" in report.errors[0]


# 5. Test Negative and Zero Amount
def test_negative_amount():
    neg_csv = "transaction_id,timestamp,sender,receiver,amount\nTX01,2026-09-18 10:00:00,A,B,-50000\nTX02,2026-09-18 10:05:00,A,B,0"
    report, txs = validator.validate_csv_text(neg_csv)
    assert report.invalid_rows == 2
    assert not report.is_acceptable_for_analysis


# 6. Test Duplicate Transaction ID Handling
def test_duplicate_transaction_id():
    dup_csv = (
        "transaction_id,timestamp,sender,receiver,amount\n"
        "TX_SAME,2026-09-18 10:00:00,A,B,50000\n"
        "TX_SAME,2026-09-18 10:05:00,B,C,48000"
    )
    report, txs = validator.validate_csv_text(dup_csv)
    assert report.valid_rows == 2
    assert len(report.warnings) >= 1
    assert txs[0].transaction_id != txs[1].transaction_id  # Auto-deduplicated


# 7. Test Graph Generation from Custom Data
def test_graph_generation_from_custom_data():
    csv_text = get_sample_csv_text()
    report, txs = validator.validate_csv_text(csv_text)
    assert report.is_acceptable_for_analysis
    g = FinancialMultiGraph()
    g.load_transactions(txs)
    assert g.get_node_count() >= 10
    assert g.get_edge_count() >= 15


# 8. Test Custom Layering Detection
def test_custom_layering_detection():
    csv_text = get_sample_csv_text()
    report, txs = validator.validate_csv_text(csv_text)
    g = FinancialMultiGraph()
    g.load_transactions(txs)
    findings = LayeringDetector(min_hops=3).detect(g)
    assert len(findings) >= 1
    assert findings[0].pattern_type.value == "LAYERING"


# 9. Test Custom Cycle Detection
def test_custom_cycle_detection():
    csv_text = get_sample_csv_text()
    report, txs = validator.validate_csv_text(csv_text)
    g = FinancialMultiGraph()
    g.load_transactions(txs)
    cycles = CircularTransferDetector().detect(g)
    assert len(cycles) >= 1
    assert "ACC_LOOP_ENTITY_Z" in cycles[0].accounts_involved


# 10. Test Custom Rapid Movement Detection
def test_custom_rapid_movement_detection():
    csv_text = get_sample_csv_text()
    report, txs = validator.validate_csv_text(csv_text)
    g = FinancialMultiGraph()
    g.load_transactions(txs)
    rapid = RapidMovementDetector(max_dwell_minutes=15.0).detect(g)
    assert len(rapid) >= 1
    assert rapid[0].metrics["dwell_time_minutes"] <= 6.0


# 11. Test Custom Fan-Out Detection
def test_custom_fan_out_detection():
    csv_text = get_sample_csv_text()
    report, txs = validator.validate_csv_text(csv_text)
    g = FinancialMultiGraph()
    g.load_transactions(txs)
    fan_out = FanPatternsDetector(min_fan_count=3).detect_fan_out(g)
    assert len(fan_out) >= 1
    dispersers = [f.metrics.get("disperser_account") for f in fan_out]
    assert "ACC_DISPERSION_NODE_X" in dispersers


# 12. Test Custom Fan-In Detection
def test_custom_fan_in_detection():
    fan_in_csv = (
        "transaction_id,timestamp,sender,receiver,amount\n"
        "T1,2026-09-18 10:00:00,FEEDER_1,AGGREGATOR_MASTER,100000\n"
        "T2,2026-09-18 10:05:00,FEEDER_2,AGGREGATOR_MASTER,100000\n"
        "T3,2026-09-18 10:10:00,FEEDER_3,AGGREGATOR_MASTER,100000"
    )
    report, txs = validator.validate_csv_text(fan_in_csv)
    g = FinancialMultiGraph()
    g.load_transactions(txs)
    fan_in = FanPatternsDetector(min_fan_count=3).detect_fan_in(g)
    assert len(fan_in) >= 1
    assert fan_in[0].metrics["aggregator_account"] == "AGGREGATOR_MASTER"


# 13. Test Custom Attack Path Reconstruction
def test_custom_attack_path():
    csv_text = get_sample_csv_text()
    report, txs = validator.validate_csv_text(csv_text)
    g = FinancialMultiGraph()
    g.load_transactions(txs)
    paths = AttackPathEngine().reconstruct_paths(g)
    assert len(paths) >= 1
    assert paths[0].source_account == "ACC_ANON_ORIGINATOR"
    assert paths[0].destination_account == "ACC_OFFSHORE_SINK_DEST"
    assert paths[0].retention_percentage > 85.0


# 14. Test Custom Role Inference
def test_custom_role_inference():
    csv_text = get_sample_csv_text()
    report, txs = validator.validate_csv_text(csv_text)
    g = FinancialMultiGraph()
    g.load_transactions(txs)
    roles = RoleInferenceEngine().infer_roles(g)
    assert roles["ACC_ANON_ORIGINATOR"].probable_role.value == "ORIGINATOR"
    assert roles["ACC_OFFSHORE_SINK_DEST"].probable_role.value == "SINK"


# 15. Test Custom Temporal Analysis
def test_custom_temporal_analysis():
    response = client.post("/api/investigate/custom", data={"csv_text": get_sample_csv_text()})
    assert response.status_code == 200
    data = response.json()
    assert len(data["temporal_stages"]) >= 2
    assert "INJECTION" in [s["stage_name"] for s in data["temporal_stages"]]


# 16. Test Custom Priority Ranking
def test_custom_priority():
    response = client.post("/api/investigate/custom", data={"csv_text": get_sample_csv_text()})
    assert response.status_code == 200
    data = response.json()
    assert len(data["priority_rankings"]) > 0
    top_p = data["priority_rankings"][0]
    assert 0 <= top_p["priority_score"] <= 100
    assert len(top_p["why_factors"]) >= 1


# 17. Test Custom DNA Generation
def test_custom_dna_generation():
    response = client.post("/api/investigate/custom", data={"csv_text": get_sample_csv_text()})
    assert response.status_code == 200
    data = response.json()
    dna = data["primary_dna"]
    assert dna is not None
    assert dna["signature"].startswith("DNA-")
    assert "RET" in dna["signature"]
    assert "VEL" in dna["signature"]
    assert len(dna["genes"]) == 6


# 18. Test Custom DNA Evidence Drill-Down
def test_custom_dna_evidence():
    response = client.post("/api/investigate/custom", data={"csv_text": get_sample_csv_text()})
    data = response.json()
    case_id = data["case_id"]
    path_id = data["attack_paths"][0]["path_id"]

    ev_resp = client.get(f"/api/dna/{case_id}/{path_id}/evidence")
    assert ev_resp.status_code == 200
    ev_data = ev_resp.json()
    assert "sha256_forensic_integrity_seal" in ev_data
    assert len(ev_data["sha256_forensic_integrity_seal"]) == 64


# 19. Test Custom DNA Similarity
def test_custom_dna_similarity():
    response = client.post("/api/investigate/custom", data={"csv_text": get_sample_csv_text()})
    data = response.json()
    similar = data["similar_cases"]
    assert len(similar) > 0
    assert similar[0]["overall_similarity_pct"] >= 60.0


# 20. Test Custom No-Suspicious-Activity Dataset
def test_custom_no_suspicious_activity():
    benign_csv = (
        "transaction_id,timestamp,sender,receiver,amount,channel\n"
        "TX_B01,2026-09-18 09:00:00,STORE_A,SUPPLIER_1,50000,NEFT\n"
        "TX_B02,2026-09-18 12:00:00,STORE_A,SUPPLIER_2,75000,NEFT\n"
        "TX_B03,2026-09-18 15:30:00,STORE_B,SUPPLIER_1,60000,IMPS"
    )
    response = client.post("/api/investigate/custom", data={"csv_text": benign_csv})
    assert response.status_code == 200
    data = response.json()
    assert data["graph"]["node_count"] == 4
    assert data["graph"]["edge_count"] == 3
    # No high-risk patterns or attack paths forced
    assert len(data["attack_paths"]) == 0
    assert len(data["patterns"]) == 0
    assert data["narrative_brief"] is not None


# 21. Test Custom Case Persistence and Trace API
def test_custom_export_and_trace():
    response = client.post("/api/investigate/custom", data={"csv_text": get_sample_csv_text()})
    data = response.json()
    case_id = data["case_id"]

    # Trace endpoint on custom case
    trace_resp = client.get(f"/api/trace/{case_id}/ACC_GATEKEEPER_MULE_1")
    assert trace_resp.status_code == 200
    trace_data = trace_resp.json()
    assert trace_data["focus_account"] == "ACC_GATEKEEPER_MULE_1"
    assert len(trace_data["upstream"]["nodes"]) >= 1


# 22. Test Existing Scenarios Still Work Perfectly
def test_existing_scenarios_still_work():
    res_g = client.get("/api/cases/SCENARIO_G")
    assert res_g.status_code == 200
    assert res_g.json()["scenario_id"] == "SCENARIO_G"

    res_a = client.get("/api/cases/SCENARIO_A")
    assert res_a.status_code == 200
    assert res_a.json()["scenario_id"] == "SCENARIO_A"


# 23. Required Integration Test (from user prompt specification)
def test_api_integration_custom_dataset():
    """
    Integration test using the prompt's exact sequence:
    TX001 2026-09-18 09:00 ACC_A ACC_B 500000
    TX002 2026-09-18 09:08 ACC_B ACC_C 490000
    TX003 2026-09-18 09:15 ACC_C ACC_D 480000
    TX004 2026-09-18 09:25 ACC_D ACC_E 470000
    """
    exact_csv = (
        "transaction_id,timestamp,sender,receiver,amount\n"
        "TX001,2026-09-18 09:00:00,ACC_A,ACC_B,500000\n"
        "TX002,2026-09-18 09:08:00,ACC_B,ACC_C,490000\n"
        "TX003,2026-09-18 09:15:00,ACC_C,ACC_D,480000\n"
        "TX004,2026-09-18 09:25:00,ACC_D,ACC_E,470000"
    )

    response = client.post("/api/investigate/custom", data={"csv_text": exact_csv})
    assert response.status_code == 200
    data = response.json()

    # Verify complete pipeline on dynamic input
    assert data["graph"]["node_count"] == 5
    assert data["graph"]["edge_count"] == 4
    assert len(data["attack_paths"]) == 1
    top_path = data["attack_paths"][0]
    assert top_path["source_account"] == "ACC_A"
    assert top_path["destination_account"] == "ACC_E"
    assert top_path["hop_count"] == 4
    assert top_path["retention_percentage"] == 94.0  # 470000 / 500000

    dna = data["primary_dna"]
    assert dna is not None
    assert "RET94" in dna["signature"]
    assert "H4" in dna["signature"]
    assert "VEL" in dna["signature"]
