"""
Historical Benchmark Reference Typologies Library for Behavioural Similarity Matching.
Contains curated synthetic cases representing known laundering typologies.
"""
from typing import List
from backend.models.dna import HistoricalCase


HISTORICAL_CASE_LIBRARY: List[HistoricalCase] = [
    HistoricalCase(
        case_id="CASE-007",
        case_title="Operation Desert Funnel (Hawala & Rapid Mule Transit)",
        typology_description="Multi-tier rapid mule forwarding with high retention (92%) and sub-15 minute transit latencies.",
        dna_signature="DNA-LAY4-RAP-RET92-VEL12-DISP3-H4",
        typology_code="LAY-RAP",
        retention_score=92.0,
        avg_dwell_minutes=12.0,
        dispersion_code="DISP3",
        hop_depth=4,
        role_sequence=["ORIGINATOR", "MULE", "MULE", "AGGREGATOR", "SINK"],
        leads_and_playbook=[
            "Inspect KYC for intermediary mule accounts (likely compromised student or dormant accounts).",
            "Cross-reference IP / device fingerprints across UPI gateway logs.",
            "Issue priority STR for aggregator beneficiary account.",
        ],
    ),
    HistoricalCase(
        case_id="CASE-014",
        case_title="Shell Company Round-Tripping Nexus",
        typology_description="Layered commercial accounts executing circular transfers with high amounts and moderate dwell times.",
        dna_signature="DNA-LAY3-CYC-RET98-VEL45-DISP1-H3",
        typology_code="LAY-CYC",
        retention_score=98.0,
        avg_dwell_minutes=45.0,
        dispersion_code="DISP1",
        hop_depth=3,
        role_sequence=["ORIGINATOR", "MULE", "MULE", "ORIGINATOR"],
        leads_and_playbook=[
            "Verify corporate registry and shared directors between entities.",
            "Inspect underlying trade invoices and GST filings for fictitious goods movement.",
        ],
    ),
    HistoricalCase(
        case_id="CASE-021",
        case_title="Micro-Smurfing Structuring Syndicate",
        typology_description="High dispersion fan-out (1 -> 6 -> 1) with small structured transfers below reporting threshold.",
        dna_signature="DNA-FAN-RET88-VEL20-DISP6-H5",
        typology_code="FAN-LAY",
        retention_score=88.0,
        avg_dwell_minutes=20.0,
        dispersion_code="DISP6",
        hop_depth=5,
        role_sequence=["ORIGINATOR", "DISPERSER", "MULE", "AGGREGATOR", "SINK"],
        leads_and_playbook=[
            "Trace initial placement source via cash deposit machines or P2P crypto gateways.",
            "Coordinate with correspondent banks for smurf tier account freezes.",
        ],
    ),
    HistoricalCase(
        case_id="CASE-035",
        case_title="Aggregator Funnel & Offshore Crypto Exit",
        typology_description="Multiple disparate feeds converging into single corporate escrow account prior to RTGS settlement.",
        dna_signature="DNA-FAN-RET95-VEL30-DISP4-H4",
        typology_code="FAN-RAP",
        retention_score=95.0,
        avg_dwell_minutes=30.0,
        dispersion_code="DISP4",
        hop_depth=4,
        role_sequence=["ORIGINATOR", "DISPERSER", "AGGREGATOR", "SINK"],
        leads_and_playbook=[
            "Review VASP / exchange settlement endpoints.",
            "Request nodal account freeze at payment gateway level.",
        ],
    ),
]


def get_historical_case_library() -> List[HistoricalCase]:
    return HISTORICAL_CASE_LIBRARY
