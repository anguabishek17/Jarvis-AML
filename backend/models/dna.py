"""
Data models for Money Trail DNA (Financial Behavioural Fingerprint) and Behavioural Similarity.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class DNAGene(BaseModel):
    gene_name: str = Field(..., description="Name of gene: Typology, Retention, Velocity, Dispersion, Topology, Role Sequence")
    gene_code: str = Field(..., description="Compact code (e.g. LAY4, RET93, VEL14, DISP1-3-1, H5)")
    value_display: str = Field(..., description="Human-readable value (e.g. '93.3% Retained', '14 mins Dwell')")
    why_explanation: str = Field(..., description="Explainable derivation of the gene")
    supporting_transaction_ids: List[str] = Field(default_factory=list, description="Direct supporting transaction IDs")
    calculation_details: Dict[str, Any] = Field(default_factory=dict, description="Numerical details (initial_amount, final_amount, etc.)")


class DNAEvidenceLink(BaseModel):
    gene_code: str = Field(...)
    initial_amount_inr: Optional[float] = None
    final_amount_inr: Optional[float] = None
    retention_pct: Optional[float] = None
    avg_dwell_minutes: Optional[float] = None
    hop_count: Optional[int] = None
    source_transactions: List[str] = Field(default_factory=list)
    narrative: str = Field(...)


class DNAEvolutionStage(BaseModel):
    stage_index: int = Field(..., description="1-indexed stage order")
    stage_name: str = Field(..., description="INJECTION, DISPERSION, LAYERING, CONVERGENCE, SINK")
    timestamp_range: str = Field(..., description="e.g. '10:00 - 10:15 IST'")
    active_dna_signature: str = Field(..., description="DNA string at this chronological point")
    new_genes_added: List[str] = Field(default_factory=list)
    volume_inr_at_stage: float = Field(default=0.0)
    accounts_active: List[str] = Field(default_factory=list)
    stage_narrative: str = Field(..., description="Forensic summary of this stage")


class MoneyTrailDNA(BaseModel):
    dna_id: str = Field(..., description="Unique DNA ID (e.g. DNA_PATH_001)")
    path_id: str = Field(..., description="Associated attack path ID")
    signature: str = Field(..., description="Deterministic compact string (e.g. DNA-LAY4-RAP98-RET93-VEL14-DISP3-H5)")
    genes: List[DNAGene] = Field(default_factory=list, description="Individual genes")
    
    # Gene values unpacked for fast comparison
    typology_code: str = Field(default="", description="e.g. LAY-RAP-DISP")
    retention_score: float = Field(default=0.0, description="0 to 100 percentage")
    velocity_score: float = Field(default=0.0, description="Dwell velocity index (lower minutes = higher score)")
    avg_dwell_minutes: float = Field(default=0.0)
    dispersion_code: str = Field(default="", description="e.g. 1-3-1")
    hop_depth: int = Field(default=0)
    role_sequence: List[str] = Field(default_factory=list, description="e.g. ['ORIGINATOR', 'MULE', 'DISPERSER', 'AGGREGATOR', 'SINK']")
    
    # Forensic Integrity Hash
    evidence_payload_sha256: str = Field(..., description="SHA-256 hash of structured evidence payload for tamper-evidence")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Evolution
    evolution_stages: List[DNAEvolutionStage] = Field(default_factory=list)


class CaseSimilarityResult(BaseModel):
    case_id: str = Field(..., description="Historical case reference (e.g. CASE-007)")
    case_title: str = Field(..., description="Title of historical reference pattern")
    overall_similarity_pct: float = Field(..., ge=0.0, le=100.0, description="Overall match percentage (e.g. 89.4%)")
    typology_similarity_pct: float = Field(default=0.0)
    retention_similarity_pct: float = Field(default=0.0)
    velocity_similarity_pct: float = Field(default=0.0)
    topology_similarity_pct: float = Field(default=0.0)
    role_sequence_similarity_pct: float = Field(default=0.0)
    dna_signature: str = Field(default="")
    known_typology_notes: str = Field(default="")
    investigative_leads: List[str] = Field(default_factory=list)


class HistoricalCase(BaseModel):
    case_id: str = Field(..., description="Unique case identifier")
    case_title: str = Field(...)
    typology_description: str = Field(...)
    dna_signature: str = Field(...)
    typology_code: str = Field(...)
    retention_score: float = Field(...)
    avg_dwell_minutes: float = Field(...)
    dispersion_code: str = Field(...)
    hop_depth: int = Field(...)
    role_sequence: List[str] = Field(default_factory=list)
    leads_and_playbook: List[str] = Field(default_factory=list)
