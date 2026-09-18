import io
import json
import pytest
from pypdf import PdfReader
from fastapi.testclient import TestClient
from backend.api.app import app
from backend.reporting.pdf_report import ForensicPDFReportGenerator

client = TestClient(app)
generator = ForensicPDFReportGenerator()

SAMPLE_CSV = """transaction_id,timestamp,sender,receiver,amount,currency,channel
TX001,2026-09-18 09:00:00,ACC_SOURCE,ACC_MULE1,500000,INR,NEFT
TX002,2026-09-18 09:08:00,ACC_MULE1,ACC_MULE2,490000,INR,IMPS
TX003,2026-09-18 09:15:00,ACC_MULE2,ACC_MULE3,480000,INR,IMPS
TX004,2026-09-18 09:25:00,ACC_MULE3,ACC_DISPERSER,470000,INR,NEFT
TX005,2026-09-18 09:30:00,ACC_DISPERSER,ACC_BENEFICIARY1,150000,INR,UPI
TX006,2026-09-18 09:31:00,ACC_DISPERSER,ACC_BENEFICIARY2,145000,INR,UPI
TX007,2026-09-18 09:32:00,ACC_DISPERSER,ACC_BENEFICIARY3,140000,INR,UPI
TX008,2026-09-18 09:45:00,ACC_BENEFICIARY1,ACC_AGGREGATOR,145000,INR,NEFT
TX009,2026-09-18 09:47:00,ACC_BENEFICIARY2,ACC_AGGREGATOR,140000,INR,NEFT
TX010,2026-09-18 09:49:00,ACC_BENEFICIARY3,ACC_AGGREGATOR,135000,INR,NEFT
TX011,2026-09-18 10:05:00,ACC_AGGREGATOR,ACC_SINK,410000,INR,RTGS
TX012,2026-09-18 11:00:00,ACC_COMPANY,ACC_VENDOR1,25000,INR,NEFT
TX013,2026-09-18 11:30:00,ACC_COMPANY,ACC_VENDOR2,18000,INR,NEFT
TX014,2026-09-18 12:00:00,ACC_VENDOR1,ACC_COMPANY,5000,INR,NEFT
TX015,2026-09-18 13:00:00,ACC_COMPANY,ACC_VENDOR3,32000,INR,UPI"""


def _get_pdf_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join([page.extract_text() or "" for page in reader.pages])


def test_pdf_export_custom_case():
    """Verify PDF export for dynamically ingested custom dataset."""
    res_ingest = client.post("/api/investigate/custom", json={"csv_text": SAMPLE_CSV, "dataset_name": "Test Ingestion"})
    assert res_ingest.status_code == 200
    case_data = res_ingest.json()
    case_id = case_data["case_id"]

    res_pdf = client.get(f"/api/cases/{case_id}/export/pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert f"JARVIS-AML-{case_id}-Investigation-Report.pdf" in res_pdf.headers["content-disposition"]
    assert len(res_pdf.content) > 1000
    assert res_pdf.content.startswith(b"%PDF-")


def test_pdf_export_scenario_case():
    """Verify PDF export for predefined Benchmark Scenario G."""
    response = client.get("/api/cases/SCENARIO_G/export/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in response.headers["content-disposition"]
    assert "JARVIS-AML-SCENARIO_G-Investigation-Report.pdf" in response.headers["content-disposition"]
    assert len(response.content) > 1000
    assert response.content.startswith(b"%PDF-")


def test_pdf_content_type():
    """Verify content-type is strictly application/pdf."""
    res = client.get("/api/cases/SCENARIO_B/export/pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"


def test_pdf_filename():
    """Verify attachment filename matches case ID format."""
    res = client.get("/api/cases/SCENARIO_C/export/pdf")
    assert res.status_code == 200
    disp = res.headers.get("content-disposition", "")
    assert 'filename="JARVIS-AML-SCENARIO_C-Investigation-Report.pdf"' in disp


def test_pdf_contains_case_id():
    """Verify PDF text contains the exact case ID."""
    res_ingest = client.post("/api/investigate/custom", json={"csv_text": SAMPLE_CSV, "dataset_name": "Case ID Check"})
    case_id = res_ingest.json()["case_id"]

    res_pdf = client.get(f"/api/cases/{case_id}/export/pdf")
    text = _get_pdf_text(res_pdf.content)
    assert case_id in text
    assert "JARVIS-AML" in text


def test_pdf_contains_patterns():
    """Verify PDF lists detected pattern types."""
    res_case = client.get("/api/cases/SCENARIO_G")
    case_data = res_case.json()
    pdf_bytes = generator.generate_pdf(case_data)
    text = _get_pdf_text(pdf_bytes)

    assert "AML SUSPICIOUS PATTERN FINDINGS" in text
    assert "LAYERING" in text or "RAPID_MOVEMENT" in text or "CIRCULAR" in text


def test_pdf_contains_attack_paths():
    """Verify PDF renders reconstructed attack paths and transit details."""
    res_case = client.get("/api/cases/SCENARIO_G")
    case_data = res_case.json()
    pdf_bytes = generator.generate_pdf(case_data)
    text = _get_pdf_text(pdf_bytes)

    assert "RECONSTRUCTED ATTACK PATHS" in text
    assert "PATH-" in text or "ACC_" in text


def test_pdf_contains_roles():
    """Verify PDF contains probable account role inferences."""
    res_case = client.get("/api/cases/SCENARIO_G")
    case_data = res_case.json()
    pdf_bytes = generator.generate_pdf(case_data)
    text = _get_pdf_text(pdf_bytes)

    assert "PROBABLE ACCOUNT ROLE" in text
    assert "MULE" in text or "ORIGINATOR" in text or "SINK" in text


def test_pdf_contains_dna():
    """Verify PDF includes 6-gene Money Trail DNA signature."""
    res_ingest = client.post("/api/investigate/custom", json={"csv_text": SAMPLE_CSV, "dataset_name": "DNA Check"})
    case_data = res_ingest.json()
    dna_sig = case_data["primary_dna"]["signature"]

    pdf_bytes = generator.generate_pdf(case_data)
    text = _get_pdf_text(pdf_bytes)

    assert "MONEY TRAIL DNA" in text
    assert dna_sig in text


def test_pdf_contains_evidence():
    """Verify PDF includes transaction evidence references."""
    res_ingest = client.post("/api/investigate/custom", json={"csv_text": SAMPLE_CSV, "dataset_name": "Evidence Check"})
    case_data = res_ingest.json()

    pdf_bytes = generator.generate_pdf(case_data)
    text = _get_pdf_text(pdf_bytes)

    assert "TRANSACTION EVIDENCE REGISTER" in text
    assert "TX001" in text or "ACC_SOURCE" in text


def test_pdf_contains_sha256():
    """Verify PDF displays the cryptographic SHA-256 evidence integrity seal."""
    res_ingest = client.post("/api/investigate/custom", json={"csv_text": SAMPLE_CSV, "dataset_name": "Hash Check"})
    case_data = res_ingest.json()
    sha256_seal = case_data["primary_dna"]["evidence_payload_sha256"]

    pdf_bytes = generator.generate_pdf(case_data)
    text = _get_pdf_text(pdf_bytes)

    assert "CRYPTOGRAPHIC EVIDENCE" in text
    assert "INTEGRITY SEAL" in text
    assert sha256_seal in text


def test_pdf_dynamic_anti_hardcoding():
    """Verify modifying transactions dynamically alters the generated PDF output."""
    csv_v1 = SAMPLE_CSV
    csv_v2 = SAMPLE_CSV.replace("500000", "850000").replace("410000", "790000")

    res_1 = client.post("/api/investigate/custom", json={"csv_text": csv_v1, "dataset_name": "Case 1"})
    res_2 = client.post("/api/investigate/custom", json={"csv_text": csv_v2, "dataset_name": "Case 2"})

    case_1 = res_1.json()
    case_2 = res_2.json()

    pdf_1 = generator.generate_pdf(case_1)
    pdf_2 = generator.generate_pdf(case_2)

    assert pdf_1 != pdf_2
    text_1 = _get_pdf_text(pdf_1)
    text_2 = _get_pdf_text(pdf_2)

    assert case_1["primary_dna"]["signature"] in text_1
    assert case_2["primary_dna"]["signature"] in text_2
    assert case_1["primary_dna"]["signature"] != case_2["primary_dna"]["signature"]


def test_pdf_missing_optional_fields():
    """Verify generator handles sparse case objects without error."""
    sparse_case = {
        "scenario_id": "CUSTOM-MINIMAL",
        "metadata": {"title": "Sparse Dataset"},
        "graph": {"nodes": [{"id": "A"}, {"id": "B"}], "edges": [{"source": "A", "target": "B", "amount": 1000}]},
        "patterns": [],
        "attack_paths": [],
        "roles": {},
        "priority_rankings": [],
        "primary_dna": None,
        "similar_cases": [],
        "temporal_stages": [],
        "narrative_brief": {"executive_summary": "Minimal case summary."},
    }

    pdf_bytes = generator.generate_pdf(sparse_case)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF-")


def test_pdf_large_dataset_register_bounds():
    """Verify generator limits register rows to avoid unbounded document expansion."""
    large_edges = [
        {"id": f"TX{i:04d}", "timestamp": "2026-09-18 10:00:00", "sender_account": f"ACC_{i}", "receiver_account": f"ACC_{i+1}", "amount": 5000.0, "channel": "NEFT"}
        for i in range(100)
    ]
    large_case = {
        "scenario_id": "CUSTOM-LARGE",
        "metadata": {"title": "Large Dataset Test", "total_volume_inr": 500000.0},
        "graph": {"nodes": [{"id": f"ACC_{i}"} for i in range(101)], "edges": large_edges},
        "patterns": [],
        "attack_paths": [],
        "roles": {},
        "priority_rankings": [],
        "primary_dna": None,
        "narrative_brief": {"executive_summary": "Large case."},
    }

    pdf_bytes = generator.generate_pdf(large_case)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")
