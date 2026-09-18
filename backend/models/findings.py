"""
Pydantic data models for investigation findings, pattern detections, attack paths, roles, and evidence chains.
"""
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class PatternType(str, Enum):
    LAYERING = "LAYERING"
    CIRCULAR_TRANSFER = "CIRCULAR_TRANSFER"
    RAPID_MOVEMENT = "RAPID_MOVEMENT"
    FAN_IN = "FAN_IN"
    FAN_OUT = "FAN_OUT"
    SMURFING = "SMURFING"


class PatternSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EvidenceItem(BaseModel):
    evidence_id: str = Field(..., description="Unique evidence reference")
    finding_title: str = Field(..., description="Short finding title")
    pattern_type: PatternType = Field(..., description="Associated pattern")
    involved_accounts: List[str] = Field(default_factory=list, description="List of account IDs")
    transaction_ids: List[str] = Field(default_factory=list, description="Supporting transaction IDs")
    timestamps: List[datetime] = Field(default_factory=list, description="Transaction timestamps")
    amounts_inr: List[float] = Field(default_factory=list, description="Transaction amounts in INR")
    dwell_time_minutes: Optional[float] = Field(default=None, description="Elapsed intermediary dwell time")
    retention_percentage: Optional[float] = Field(default=None, description="Percentage of funds retained")
    associated_path_id: Optional[str] = Field(default=None, description="Linked attack path ID")
    narrative_explanation: str = Field(..., description="Human-readable forensic explanation")


class PatternFinding(BaseModel):
    pattern_id: str = Field(..., description="Unique pattern detection ID")
    pattern_type: PatternType = Field(..., description="Type of AML pattern")
    severity: PatternSeverity = Field(default=PatternSeverity.HIGH, description="Risk severity")
    title: str = Field(..., description="Descriptive title")
    description: str = Field(..., description="Detailed explanation of pattern mechanics")
    accounts_involved: List[str] = Field(default_factory=list)
    transaction_ids: List[str] = Field(default_factory=list)
    total_volume_inr: float = Field(default=0.0)
    metrics: Dict[str, Any] = Field(default_factory=dict, description="e.g. hop count, forwarding ratio, cycle duration")
    evidence: List[EvidenceItem] = Field(default_factory=list)
    confidence_score: float = Field(default=0.85, ge=0.0, le=1.0)


class AttackPath(BaseModel):
    path_id: str = Field(..., description="Unique path ID (e.g. PATH_001)")
    source_account: str = Field(..., description="Originating account")
    destination_account: str = Field(..., description="Final sink account")
    intermediate_accounts: List[str] = Field(default_factory=list, description="Transit/mule accounts")
    account_sequence: List[str] = Field(default_factory=list, description="Complete sequence of accounts in path")
    transaction_ids: List[str] = Field(default_factory=list, description="Transactions along this path")
    hop_count: int = Field(..., description="Number of hops/transfers")
    total_inflow_inr: float = Field(..., description="Initial source amount in INR")
    total_outflow_inr: float = Field(..., description="Final sink amount in INR")
    retained_amount_inr: float = Field(..., description="Amount retained across path")
    retention_percentage: float = Field(..., description="Percentage of original money retained at sink")
    start_time: datetime = Field(..., description="Path start timestamp")
    end_time: datetime = Field(..., description="Path end timestamp")
    elapsed_minutes: float = Field(..., description="Total transit duration in minutes")
    associated_patterns: List[PatternType] = Field(default_factory=list)
    risk_rank: int = Field(default=1, description="Priority ranking among extracted paths")
    dna_signature: Optional[str] = Field(default=None, description="Generated Money Trail DNA signature")


class AccountRole(str, Enum):
    ORIGINATOR = "ORIGINATOR"
    MULE = "MULE"
    DISPERSER = "DISPERSER"
    AGGREGATOR = "AGGREGATOR"
    SINK = "SINK"
    LEGITIMATE = "LEGITIMATE"


class AccountRoleHypothesis(BaseModel):
    account_id: str = Field(..., description="Account identifier")
    probable_role: AccountRole = Field(..., description="Inferred operational role hypothesis")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (e.g. 0.88)")
    evidence_signals: List[str] = Field(default_factory=list, description="List of observable evidence signals")
    inflow_total_inr: float = Field(default=0.0)
    outflow_total_inr: float = Field(default=0.0)
    forwarding_ratio: float = Field(default=0.0)
    avg_dwell_time_minutes: float = Field(default=0.0)
    in_degree: int = Field(default=0)
    out_degree: int = Field(default=0)
    betweenness_centrality: float = Field(default=0.0)
    participating_patterns: List[str] = Field(default_factory=list)


class SuspiciousCommunity(BaseModel):
    community_id: str = Field(..., description="Unique community ID (e.g. COMM_01)")
    members: List[str] = Field(default_factory=list, description="Member account IDs")
    internal_volume_inr: float = Field(default=0.0)
    external_volume_inr: float = Field(default=0.0)
    density: float = Field(default=0.0)
    dominant_typology: str = Field(default="")
    primary_mules: List[str] = Field(default_factory=list)


class InvestigationPriorityItem(BaseModel):
    account_id: str = Field(..., description="Account ID")
    priority_score: int = Field(..., ge=0, le=100, description="Triage priority score (0-100)")
    probable_role: AccountRole = Field(...)
    why_factors: List[str] = Field(default_factory=list, description="Transparent itemized score reasons")
    pattern_count: int = Field(default=0)
    path_appearances: int = Field(default=0)
    total_volume_inr: float = Field(default=0.0)
    centrality_rank: str = Field(default="MEDIUM")
