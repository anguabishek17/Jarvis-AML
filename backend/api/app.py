"""
JARVIS-AML: FastAPI Backend Application.
REST API providing comprehensive investigation intelligence, financial graphs, pattern findings,
attack paths, account role hypotheses, temporal stages, Money Trail DNA, and custom dataset ingestion.
"""
from datetime import datetime
import json
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query, Request, UploadFile, File, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from backend.models.transaction import Transaction, Account, ScenarioMetadata
from backend.models.findings import PatternFinding, AttackPath, AccountRoleHypothesis, InvestigationPriorityItem
from backend.models.dna import MoneyTrailDNA, CaseSimilarityResult
from backend.graph.financial_graph import FinancialMultiGraph
from backend.detectors.layering_detector import LayeringDetector
from backend.detectors.circular_detector import CircularTransferDetector
from backend.detectors.rapid_movement_detector import RapidMovementDetector
from backend.detectors.fan_patterns_detector import FanPatternsDetector
from backend.analytics.attack_path_engine import AttackPathEngine
from backend.analytics.role_inference import RoleInferenceEngine
from backend.analytics.temporal_engine import TemporalEngine
from backend.analytics.priority_engine import InvestigationPriorityEngine
from backend.dna.dna_engine import MoneyTrailDNAEngine
from backend.dna.dna_similarity import BehaviouralSimilarityEngine
from backend.narrative.storyline_engine import StorylineEngine
from backend.data.scenarios import get_all_scenarios
from backend.ingestion.validator import TransactionValidator, ValidationReport
from backend.ingestion.sample_generator import get_sample_csv_text
from backend.reporting.pdf_report import ForensicPDFReportGenerator


app = FastAPI(
    title="JARVIS-AML Intelligence API",
    description="AI-Powered Anti-Money-Laundering Investigation & Money Trail Intelligence System",
    version="1.0.0",
)

# Enable CORS for local dev and frontend workstation
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InvestigationPipeline:
    """Orchestrates end-to-end multi-layer intelligence analysis on a financial graph."""

    def __init__(self):
        self.layering_det = LayeringDetector()
        self.circular_det = CircularTransferDetector()
        self.rapid_det = RapidMovementDetector()
        self.fan_det = FanPatternsDetector()
        self.path_engine = AttackPathEngine()
        self.role_engine = RoleInferenceEngine()
        self.temporal_engine = TemporalEngine()
        self.priority_engine = InvestigationPriorityEngine()
        self.dna_engine = MoneyTrailDNAEngine()
        self.similarity_engine = BehaviouralSimilarityEngine()
        self.storyline_engine = StorylineEngine()

    def analyze_graph(self, graph: FinancialMultiGraph, scenario_id: str = "CUSTOM") -> Dict[str, Any]:
        # 1. AML Detectors
        findings: List[PatternFinding] = []
        findings.extend(self.layering_det.detect(graph))
        findings.extend(self.circular_det.detect(graph))
        findings.extend(self.rapid_det.detect(graph))
        findings.extend(self.fan_det.detect_all(graph))

        # 2. Map patterns by account
        pattern_map = {}
        for f in findings:
            for acc in f.accounts_involved:
                if acc not in pattern_map:
                    pattern_map[acc] = set()
                pattern_map[acc].add(f.pattern_type)

        # 3. Account Role Inference
        roles = self.role_engine.infer_roles(graph, findings)

        # 4. Attack Path Reconstruction
        attack_paths = self.path_engine.reconstruct_paths(graph, pattern_map)

        # 5. Network Communities
        communities = graph.detect_communities()

        # 6. Temporal Stages
        temporal_stages = self.temporal_engine.analyze_stages(graph, roles, findings)

        # 7. Investigation Priority Scoring (0-100)
        priority_rankings = self.priority_engine.compute_priority_rankings(graph, roles, findings, attack_paths)

        # 8. Money Trail DNA & Similarity
        dna_objects: List[MoneyTrailDNA] = []
        for path in attack_paths:
            dna = self.dna_engine.generate_dna_for_path(path, graph, roles, findings)
            dna_objects.append(dna)
            path.dna_signature = dna.signature

        primary_dna = dna_objects[0] if dna_objects else None
        similar_cases = self.similarity_engine.find_similar_cases(primary_dna) if primary_dna else []

        # 9. Narrative & Storyline
        graph_dict = graph.to_dict()
        narrative_brief = self.storyline_engine.generate_executive_summary(
            scenario_id=scenario_id,
            graph_data=graph_dict,
            findings=findings,
            attack_paths=attack_paths,
            dna=primary_dna,
            similar_cases=similar_cases,
        )
        chronological_storyline = self.storyline_engine.generate_chronological_storyline(
            attack_paths=attack_paths,
            graph_data=graph_dict,
            roles=roles,
        )

        return {
            "scenario_id": scenario_id,
            "graph": graph_dict,
            "patterns": [f.model_dump() for f in findings],
            "attack_paths": [p.model_dump() for p in attack_paths],
            "roles": {k: v.model_dump() for k, v in roles.items()},
            "communities": communities,
            "temporal_stages": temporal_stages,
            "priority_rankings": [pr.model_dump() for pr in priority_rankings],
            "dna_fingerprints": [d.model_dump() for d in dna_objects],
            "primary_dna": primary_dna.model_dump() if primary_dna else None,
            "similar_cases": [sc.model_dump() for sc in similar_cases],
            "narrative_brief": narrative_brief,
            "chronological_storyline": chronological_storyline,
        }


pipeline = InvestigationPipeline()
validator = TransactionValidator()
pdf_generator = ForensicPDFReportGenerator()
SCENARIOS_CACHE = get_all_scenarios()
CUSTOM_CASES_REGISTRY: Dict[str, Dict[str, Any]] = {}
CUSTOM_GRAPHS_REGISTRY: Dict[str, FinancialMultiGraph] = {}


def generate_custom_case_id() -> str:
    date_str = datetime.utcnow().strftime("%Y%m%d")
    count = len(CUSTOM_CASES_REGISTRY) + 1
    return f"CUSTOM-{date_str}-{count:03d}"


@app.get("/api/health")
def health_check():
    return {"status": "ONLINE", "system": "JARVIS-AML Intelligence Platform", "version": "1.0.0"}


@app.get("/api/scenarios")
def list_scenarios():
    """List all available benchmark scenarios and registered custom cases."""
    results = []
    # Predefined Scenarios
    for sc_id, (meta, accs, txs) in SCENARIOS_CACHE.items():
        results.append({
            "scenario_id": meta.scenario_id,
            "title": meta.title,
            "description": meta.description,
            "total_volume_inr": meta.total_volume_inr,
            "account_count": len(accs),
            "transaction_count": len(txs),
            "primary_typology": meta.primary_typology,
            "difficulty": meta.difficulty,
            "is_custom": False,
        })
    # Custom Cases
    for case_id, case_data in CUSTOM_CASES_REGISTRY.items():
        meta = case_data.get("metadata", {})
        results.append({
            "scenario_id": case_id,
            "title": meta.get("title", f"Custom Dataset ({case_id})"),
            "description": meta.get("description", "User-submitted custom transaction dataset"),
            "total_volume_inr": meta.get("total_volume_inr", 0.0),
            "account_count": meta.get("account_count", case_data.get("graph", {}).get("node_count", 0)),
            "transaction_count": meta.get("transaction_count", case_data.get("graph", {}).get("edge_count", 0)),
            "primary_typology": meta.get("primary_typology", "CUSTOM_INGESTION"),
            "difficulty": "CUSTOM",
            "is_custom": True,
        })
    return results


@app.get("/api/cases/{scenario_id}")
def get_case_investigation(scenario_id: str):
    """Run full intelligence analysis pipeline for a scenario or return registered custom case."""
    sc_id_upper = scenario_id.upper()

    # Check Custom Registry first
    if scenario_id in CUSTOM_CASES_REGISTRY:
        return CUSTOM_CASES_REGISTRY[scenario_id]
    if sc_id_upper in CUSTOM_CASES_REGISTRY:
        return CUSTOM_CASES_REGISTRY[sc_id_upper]

    # Check Predefined Scenarios
    if sc_id_upper in SCENARIOS_CACHE:
        meta, accounts, transactions = SCENARIOS_CACHE[sc_id_upper]
        graph = FinancialMultiGraph()
        graph.load_transactions(transactions, accounts)

        result = pipeline.analyze_graph(graph, scenario_id=meta.scenario_id)
        result["metadata"] = meta.model_dump()
        return result

    raise HTTPException(status_code=404, detail=f"Case or Scenario '{scenario_id}' not found.")


@app.api_route("/api/cases/{scenario_id}/export/pdf", methods=["GET", "OPTIONS"])
@app.api_route("/api/cases/{scenario_id}/export/pdf/", methods=["GET", "OPTIONS"])
def export_case_pdf(scenario_id: str, request: Request):
    """
    Dynamically generates and returns a forensic investigation PDF report
    for the specified scenario or custom case.
    """
    if request.method == "OPTIONS":
        return Response(status_code=200)

    # Obtain case intelligence dossier
    case_data = get_case_investigation(scenario_id)

    try:
        pdf_bytes = pdf_generator.generate_pdf(case_data)
        safe_case_id = scenario_id.replace(" ", "_").replace("/", "_")
        filename = f"JARVIS-AML-{safe_case_id}-Investigation-Report.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition",
            },
        )
    except Exception as e:
        print(f"[PDFExport] Error generating PDF for {scenario_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate investigation PDF: {str(e)}")


@app.get("/api/trace/{scenario_id}/{account_id}")
def trace_account_flow(scenario_id: str, account_id: str, depth: int = Query(2, ge=1, le=5)):
    """Interactive Counterfactual Upstream/Downstream 2-hop tracing."""
    sc_id_upper = scenario_id.upper()

    if scenario_id in CUSTOM_GRAPHS_REGISTRY:
        graph = CUSTOM_GRAPHS_REGISTRY[scenario_id]
    elif sc_id_upper in CUSTOM_GRAPHS_REGISTRY:
        graph = CUSTOM_GRAPHS_REGISTRY[sc_id_upper]
    elif sc_id_upper in SCENARIOS_CACHE:
        meta, accounts, transactions = SCENARIOS_CACHE[sc_id_upper]
        graph = FinancialMultiGraph()
        graph.load_transactions(transactions, accounts)
    else:
        raise HTTPException(status_code=404, detail=f"Case '{scenario_id}' not found.")

    upstream = graph.trace_upstream(account_id, max_depth=depth)
    downstream = graph.trace_downstream(account_id, max_depth=depth)
    neighborhood = graph.extract_2hop_neighborhood(account_id)

    return {
        "scenario_id": scenario_id,
        "focus_account": account_id,
        "upstream": upstream,
        "downstream": downstream,
        "neighborhood_2hop": neighborhood,
    }


@app.get("/api/dna/{scenario_id}")
def get_scenario_dna(scenario_id: str):
    """Get all generated Money Trail DNA fingerprints for a scenario or custom case."""
    case_data = get_case_investigation(scenario_id)
    return {
        "scenario_id": scenario_id,
        "dna_fingerprints": case_data.get("dna_fingerprints", []),
        "primary_dna": case_data.get("primary_dna"),
    }


@app.get("/api/dna/{scenario_id}/{path_id}/similar")
def get_dna_similar_cases(scenario_id: str, path_id: str):
    """Get behaviourally similar historical cases for a specific attack path DNA."""
    case_data = get_case_investigation(scenario_id)
    target_dna = None
    for d in case_data.get("dna_fingerprints", []):
        if d.get("path_id") == path_id or d.get("dna_id") == path_id:
            target_dna = MoneyTrailDNA(**d)
            break

    if not target_dna and case_data.get("primary_dna"):
        target_dna = MoneyTrailDNA(**case_data.get("primary_dna"))

    if not target_dna:
        raise HTTPException(status_code=404, detail=f"No DNA fingerprint found for path '{path_id}'.")

    similar = pipeline.similarity_engine.find_similar_cases(target_dna)
    return {
        "path_id": path_id,
        "current_dna_signature": target_dna.signature,
        "similar_cases": [s.model_dump() for s in similar],
    }


@app.get("/api/dna/{scenario_id}/{path_id}/evidence")
def get_dna_evidence_audit(scenario_id: str, path_id: str):
    """Detailed evidence breakdown, mathematical parameters, and SHA-256 forensic verification seal."""
    case_data = get_case_investigation(scenario_id)
    target_dna = None
    for d in case_data.get("dna_fingerprints", []):
        if d.get("path_id") == path_id or d.get("dna_id") == path_id:
            target_dna = d
            break

    if not target_dna and case_data.get("primary_dna"):
        target_dna = case_data.get("primary_dna")

    if not target_dna:
        raise HTTPException(status_code=404, detail="DNA evidence not found.")

    return {
        "path_id": path_id,
        "signature": target_dna.get("signature"),
        "sha256_forensic_integrity_seal": target_dna.get("evidence_payload_sha256"),
        "genes": target_dna.get("genes"),
        "evolution_stages": target_dna.get("evolution_stages"),
        "role_sequence": target_dna.get("role_sequence"),
    }


@app.get("/api/investigate/sample-csv")
def get_sample_csv():
    """Returns downloadable benchmark sample CSV."""
    csv_text = get_sample_csv_text()
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=jarvis_custom_demo.csv"},
    )


@app.api_route("/api/investigate/validate", methods=["GET", "POST", "OPTIONS"])
@app.api_route("/api/investigate/validate/", methods=["GET", "POST", "OPTIONS"])
async def validate_transactions_input(request: Request):
    """Pre-analysis validation endpoint. Accepts CSV file, form data, JSON payload, or raw text."""
    if request.method == "OPTIONS":
        return Response(status_code=200)

    if request.method == "GET":
        return {
            "status": "READY",
            "endpoint": "/api/investigate/validate",
            "accepted_methods": ["POST"],
            "total_rows": 0,
            "valid_rows": 0,
            "invalid_rows": 0,
            "total_volume_inr": 0.0,
            "is_acceptable_for_analysis": False,
            "message": "Send a POST request with transaction CSV or JSON payload to validate."
        }

    content_type = request.headers.get("content-type", "")
    text_content = ""
    raw_tx_array = None
    filename = "unknown"

    if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        if "file" in form and hasattr(form["file"], "read"):
            filename = getattr(form["file"], "filename", "upload.csv")
            file_bytes = await form["file"].read()
            text_content = file_bytes.decode("utf-8", errors="replace")
        if not text_content and "csv_text" in form:
            text_content = str(form["csv_text"])
    elif "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, dict):
                if "transactions" in body and isinstance(body["transactions"], list):
                    raw_tx_array = body["transactions"]
                elif "csv_text" in body:
                    text_content = str(body["csv_text"])
            elif isinstance(body, list):
                raw_tx_array = body
        except Exception as e:
            print(f"[CustomAnalysis] Error parsing JSON body: {e}")
    else:
        body_bytes = await request.body()
        text_content = body_bytes.decode("utf-8", errors="replace")

    print(f"[CustomAnalysis] Validate called via {request.method}. Content-Type: {content_type}, Filename: {filename}, Characters: {len(text_content)}")

    if raw_tx_array is not None:
        if not raw_tx_array:
            return ValidationReport(errors=["Submitted transaction list is empty."])
        headers = list(raw_tx_array[0].keys()) if isinstance(raw_tx_array[0], dict) else []
        report, _ = validator.validate_dict_records(raw_tx_array, headers)
        return report

    report, _ = validator.validate_csv_text(text_content)
    print(f"[CustomAnalysis] Validation Report: Total={report.total_rows}, Valid={report.valid_rows}, Invalid={report.invalid_rows}, Vol=INR {report.total_volume_inr}")
    return report


@app.api_route("/api/investigate/custom", methods=["GET", "POST", "OPTIONS"])
@app.api_route("/api/investigate/custom/", methods=["GET", "POST", "OPTIONS"])
async def investigate_custom_dataset(request: Request):
    """
    Main Custom Ingestion Endpoint:
    Accepts CSV file upload, form data, JSON payload, or raw text.
    Validates data, builds dynamic FinancialMultiGraph, runs entire JARVIS-AML investigation pipeline,
    registers case in session cache, and returns complete unified dossier.
    """
    if request.method == "OPTIONS":
        return Response(status_code=200)

    if request.method == "GET":
        return {
            "status": "READY",
            "endpoint": "/api/investigate/custom",
            "accepted_methods": ["POST"],
            "message": "Send a POST request with transaction CSV or JSON payload to run the JARVIS-AML pipeline."
        }

    content_type = request.headers.get("content-type", "")
    text_content = ""
    raw_tx_array = None
    dataset_name = None
    filename = "custom_dataset"

    if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        dataset_name = str(form.get("dataset_name") or "")
        if "file" in form and hasattr(form["file"], "read"):
            filename = getattr(form["file"], "filename", "upload.csv")
            file_bytes = await form["file"].read()
            text_content = file_bytes.decode("utf-8", errors="replace")
        if not text_content and "csv_text" in form:
            text_content = str(form["csv_text"])
    elif "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, dict):
                dataset_name = body.get("dataset_name")
                if "transactions" in body and isinstance(body["transactions"], list):
                    raw_tx_array = body["transactions"]
                elif "csv_text" in body:
                    text_content = str(body["csv_text"])
            elif isinstance(body, list):
                raw_tx_array = body
        except Exception as e:
            print(f"[CustomAnalysis] Error parsing JSON body in custom: {e}")
    else:
        body_bytes = await request.body()
        text_content = body_bytes.decode("utf-8", errors="replace")

    print(f"[CustomAnalysis] Custom pipeline called via {request.method}. Filename: {filename}, Characters: {len(text_content)}")

    if raw_tx_array is not None:
        if not raw_tx_array:
            raise HTTPException(status_code=400, detail="Submitted transaction array is empty.")
        headers = list(raw_tx_array[0].keys()) if isinstance(raw_tx_array[0], dict) else []
        report, valid_txs = validator.validate_dict_records(raw_tx_array, headers)
    else:
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="No transaction data provided. Provide CSV file, text, or JSON.")
        report, valid_txs = validator.validate_csv_text(text_content)

    if not report.is_acceptable_for_analysis or not valid_txs:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Transaction validation failed.",
                "errors": report.errors,
                "warnings": report.warnings,
            },
        )

    # Generate Case ID
    case_id = generate_custom_case_id()

    # Construct Dynamic Financial MultiGraph
    graph = FinancialMultiGraph()
    graph.load_transactions(valid_txs)

    # Run Complete Investigation Pipeline
    result = pipeline.analyze_graph(graph, scenario_id=case_id)

    # Add Custom Metadata
    meta = {
        "scenario_id": case_id,
        "title": dataset_name or f"Custom Dataset ({case_id})",
        "description": f"Analyzed user-provided dataset with {len(valid_txs)} transactions across {report.unique_accounts_count} accounts.",
        "total_volume_inr": report.total_volume_inr,
        "account_count": report.unique_accounts_count,
        "transaction_count": len(valid_txs),
        "primary_typology": "CUSTOM_INGESTION",
        "difficulty": "CUSTOM",
        "is_custom": True,
        "validation_summary": report.model_dump(),
    }
    result["metadata"] = meta
    result["validation_report"] = report.model_dump()
    result["case_id"] = case_id
    result["source"] = "custom"
    result["status"] = "completed"

    # Store in registries for session exploration & tracing
    CUSTOM_CASES_REGISTRY[case_id] = result
    CUSTOM_GRAPHS_REGISTRY[case_id] = graph

    print(f"[CustomAnalysis] Analysis complete for {case_id}: Nodes={graph.get_node_count()}, Edges={graph.get_edge_count()}, Paths={len(result['attack_paths'])}")
    return result


# Serve frontend static assets if frontend directory exists
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
