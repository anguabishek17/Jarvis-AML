"""
Pre-built Benchmark Scenarios with realistic Indian Financial context (INR ₹, UPI/IMPS/NEFT/RTGS).
Includes Scenarios A through G, with Scenario G as the primary comprehensive multi-stage laundering demonstration.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from backend.models.transaction import Transaction, Account, PaymentChannel, TransactionType, TransactionStatus, ScenarioMetadata


def create_scenario_a_normal() -> Tuple[ScenarioMetadata, List[Account], List[Transaction]]:
    """Scenario A: Normal Commercial & Payroll Activity."""
    base_time = datetime(2026, 9, 15, 9, 0, 0)
    meta = ScenarioMetadata(
        scenario_id="SCENARIO_A",
        title="Scenario A — Legitimate Commercial & Payroll Flows",
        description="Routine enterprise salary disbursement and merchant settlements with normal dwell times.",
        total_volume_inr=1250000.0,
        account_count=6,
        transaction_count=5,
        primary_typology="BENIGN_COMMERCIAL",
        difficulty="LOW",
    )
    accounts = [
        Account(account_id="ACC_TECHCORP_PAYROLL", account_holder_name="TechCorp India Pvt Ltd", account_type="CURRENT", bank_name="State Bank of India"),
        Account(account_id="ACC_EMP_01", account_holder_name="Aarav Sharma", account_type="SAVINGS", bank_name="HDFC Bank"),
        Account(account_id="ACC_EMP_02", account_holder_name="Priya Patel", account_type="SAVINGS", bank_name="ICICI Bank"),
        Account(account_id="ACC_EMP_03", account_holder_name="Rohan Verma", account_type="SAVINGS", bank_name="Axis Bank"),
        Account(account_id="ACC_MERCHANT_OFFICE", account_holder_name="Office Supplies Hub", account_type="CURRENT", bank_name="Kotak Bank"),
        Account(account_id="ACC_LANDLORD_RE", account_holder_name="Premier Properties", account_type="CURRENT", bank_name="HDFC Bank"),
    ]
    transactions = [
        Transaction(transaction_id="TXN_A_001", timestamp=base_time, sender_account="ACC_TECHCORP_PAYROLL", receiver_account="ACC_EMP_01", amount=250000.0, channel=PaymentChannel.NEFT, remarks="Monthly Salary"),
        Transaction(transaction_id="TXN_A_002", timestamp=base_time + timedelta(minutes=5), sender_account="ACC_TECHCORP_PAYROLL", receiver_account="ACC_EMP_02", amount=300000.0, channel=PaymentChannel.NEFT, remarks="Monthly Salary"),
        Transaction(transaction_id="TXN_A_003", timestamp=base_time + timedelta(minutes=10), sender_account="ACC_TECHCORP_PAYROLL", receiver_account="ACC_EMP_03", amount=200000.0, channel=PaymentChannel.NEFT, remarks="Monthly Salary"),
        Transaction(transaction_id="TXN_A_004", timestamp=base_time + timedelta(hours=4), sender_account="ACC_TECHCORP_PAYROLL", receiver_account="ACC_MERCHANT_OFFICE", amount=150000.0, channel=PaymentChannel.IMPS, remarks="Hardware Supplies"),
        Transaction(transaction_id="TXN_A_005", timestamp=base_time + timedelta(hours=6), sender_account="ACC_TECHCORP_PAYROLL", receiver_account="ACC_LANDLORD_RE", amount=350000.0, channel=PaymentChannel.RTGS, remarks="Office Rent Sept"),
    ]
    return meta, accounts, transactions


def create_scenario_b_layering() -> Tuple[ScenarioMetadata, List[Account], List[Transaction]]:
    """Scenario B: Classic Multi-Hop Sequential Layering."""
    base_time = datetime(2026, 9, 15, 10, 0, 0)
    meta = ScenarioMetadata(
        scenario_id="SCENARIO_B",
        title="Scenario B — Classic Multi-Hop Layering Trail",
        description="Sequential transfer chain across 5 accounts designed to distance funds from source.",
        total_volume_inr=1900000.0,
        account_count=5,
        transaction_count=4,
        primary_typology="LAYERING",
        difficulty="MEDIUM",
    )
    accounts = [
        Account(account_id="ACC_ORIGINATOR_B", account_holder_name="Nexus Holdings", account_type="CURRENT", bank_name="HDFC Bank"),
        Account(account_id="ACC_MULE_B1", account_holder_name="Vikas Enterprises", account_type="SAVINGS", bank_name="ICICI Bank"),
        Account(account_id="ACC_MULE_B2", account_holder_name="Sunrise Trading", account_type="SAVINGS", bank_name="Axis Bank"),
        Account(account_id="ACC_MULE_B3", account_holder_name="Delta Logistics", account_type="SAVINGS", bank_name="Kotak Bank"),
        Account(account_id="ACC_SINK_B", account_holder_name="Zenith Offshore Capital", account_type="CURRENT", bank_name="State Bank of India"),
    ]
    transactions = [
        Transaction(transaction_id="TXN_B_001", timestamp=base_time, sender_account="ACC_ORIGINATOR_B", receiver_account="ACC_MULE_B1", amount=500000.0, channel=PaymentChannel.RTGS, remarks="Consulting Advance"),
        Transaction(transaction_id="TXN_B_002", timestamp=base_time + timedelta(minutes=15), sender_account="ACC_MULE_B1", receiver_account="ACC_MULE_B2", amount=480000.0, channel=PaymentChannel.IMPS, remarks="Settlement Part 1"),
        Transaction(transaction_id="TXN_B_003", timestamp=base_time + timedelta(minutes=32), sender_account="ACC_MULE_B2", receiver_account="ACC_MULE_B3", amount=470000.0, channel=PaymentChannel.IMPS, remarks="Contractor Fee"),
        Transaction(transaction_id="TXN_B_004", timestamp=base_time + timedelta(minutes=48), sender_account="ACC_MULE_B3", receiver_account="ACC_SINK_B", amount=450000.0, channel=PaymentChannel.RTGS, remarks="Final Settlement"),
    ]
    return meta, accounts, transactions


def create_scenario_c_circular() -> Tuple[ScenarioMetadata, List[Account], List[Transaction]]:
    """Scenario C: Circular Transfer / Round-Tripping Loop."""
    base_time = datetime(2026, 9, 15, 11, 0, 0)
    meta = ScenarioMetadata(
        scenario_id="SCENARIO_C",
        title="Scenario C — Circular Round-Tripping Syndicate",
        description="Fictitious trade circulation between 3 linked corporate entities returning to the originator.",
        total_volume_inr=2350000.0,
        account_count=3,
        transaction_count=3,
        primary_typology="CIRCULAR_TRANSFER",
        difficulty="MEDIUM",
    )
    accounts = [
        Account(account_id="ACC_CORP_ALPHA", account_holder_name="Alpha Global Exim", account_type="CURRENT", bank_name="HDFC Bank"),
        Account(account_id="ACC_CORP_BETA", account_holder_name="Beta Commodity Traders", account_type="CURRENT", bank_name="ICICI Bank"),
        Account(account_id="ACC_CORP_GAMMA", account_holder_name="Gamma Trade Link", account_type="CURRENT", bank_name="Axis Bank"),
    ]
    transactions = [
        Transaction(transaction_id="TXN_C_001", timestamp=base_time, sender_account="ACC_CORP_ALPHA", receiver_account="ACC_CORP_BETA", amount=800000.0, channel=PaymentChannel.RTGS, remarks="Machinery Invoice 101"),
        Transaction(transaction_id="TXN_C_002", timestamp=base_time + timedelta(minutes=25), sender_account="ACC_CORP_BETA", receiver_account="ACC_CORP_GAMMA", amount=780000.0, channel=PaymentChannel.RTGS, remarks="Raw Material Subcontract"),
        Transaction(transaction_id="TXN_C_003", timestamp=base_time + timedelta(minutes=50), sender_account="ACC_CORP_GAMMA", receiver_account="ACC_CORP_ALPHA", amount=770000.0, channel=PaymentChannel.RTGS, remarks="Consulting Rebate"),
    ]
    return meta, accounts, transactions


def create_scenario_d_rapid_movement() -> Tuple[ScenarioMetadata, List[Account], List[Transaction]]:
    """Scenario D: High-Velocity Rapid Pass-Through Mules."""
    base_time = datetime(2026, 9, 15, 12, 0, 0)
    meta = ScenarioMetadata(
        scenario_id="SCENARIO_D",
        title="Scenario D — High-Velocity Rapid Pass-Through Mule",
        description="Sub-5 minute dwell forwarding at an intermediate transit account with 98% retention.",
        total_volume_inr=990000.0,
        account_count=3,
        transaction_count=2,
        primary_typology="RAPID_MOVEMENT",
        difficulty="LOW",
    )
    accounts = [
        Account(account_id="ACC_FEEDER_D", account_holder_name="Anonymous Inflow Source", account_type="SAVINGS", bank_name="State Bank of India"),
        Account(account_id="ACC_RAPID_MULE_D", account_holder_name="Karan Quick-Transit Mule", account_type="SAVINGS", bank_name="Kotak Bank"),
        Account(account_id="ACC_EXIT_D", account_holder_name="Overseas Crypto Ramp", account_type="CURRENT", bank_name="HDFC Bank"),
    ]
    transactions = [
        Transaction(transaction_id="TXN_D_001", timestamp=base_time, sender_account="ACC_FEEDER_D", receiver_account="ACC_RAPID_MULE_D", amount=500000.0, channel=PaymentChannel.IMPS, remarks="Urgent Transfer"),
        Transaction(transaction_id="TXN_D_002", timestamp=base_time + timedelta(minutes=4), sender_account="ACC_RAPID_MULE_D", receiver_account="ACC_EXIT_D", amount=490000.0, channel=PaymentChannel.UPI, remarks="Immediate Settlement"),
    ]
    return meta, accounts, transactions


def create_scenario_e_fan_out() -> Tuple[ScenarioMetadata, List[Account], List[Transaction]]:
    """Scenario E: Fan-Out Smurfing / Structuring."""
    base_time = datetime(2026, 9, 15, 13, 0, 0)
    meta = ScenarioMetadata(
        scenario_id="SCENARIO_E",
        title="Scenario E — Fan-Out Structuring / Smurfing",
        description="One master disperser splitting ₹15,00,000 across 5 smurf accounts below monitoring thresholds.",
        total_volume_inr=1500000.0,
        account_count=6,
        transaction_count=5,
        primary_typology="FAN_OUT",
        difficulty="MEDIUM",
    )
    accounts = [
        Account(account_id="ACC_MASTER_DISPERSER", account_holder_name="Grand Meridian Capital", account_type="CURRENT", bank_name="HDFC Bank"),
        Account(account_id="ACC_SMURF_E1", account_holder_name="Smurf Tier A", account_type="SAVINGS", bank_name="ICICI Bank"),
        Account(account_id="ACC_SMURF_E2", account_holder_name="Smurf Tier B", account_type="SAVINGS", bank_name="Axis Bank"),
        Account(account_id="ACC_SMURF_E3", account_holder_name="Smurf Tier C", account_type="SAVINGS", bank_name="Kotak Bank"),
        Account(account_id="ACC_SMURF_E4", account_holder_name="Smurf Tier D", account_type="SAVINGS", bank_name="State Bank of India"),
        Account(account_id="ACC_SMURF_E5", account_holder_name="Smurf Tier E", account_type="SAVINGS", bank_name="Punjab National Bank"),
    ]
    transactions = [
        Transaction(transaction_id="TXN_E_001", timestamp=base_time, sender_account="ACC_MASTER_DISPERSER", receiver_account="ACC_SMURF_E1", amount=300000.0, channel=PaymentChannel.IMPS, remarks="Advisory 1"),
        Transaction(transaction_id="TXN_E_002", timestamp=base_time + timedelta(minutes=6), sender_account="ACC_MASTER_DISPERSER", receiver_account="ACC_SMURF_E2", amount=300000.0, channel=PaymentChannel.IMPS, remarks="Advisory 2"),
        Transaction(transaction_id="TXN_E_003", timestamp=base_time + timedelta(minutes=12), sender_account="ACC_MASTER_DISPERSER", receiver_account="ACC_SMURF_E3", amount=300000.0, channel=PaymentChannel.IMPS, remarks="Advisory 3"),
        Transaction(transaction_id="TXN_E_004", timestamp=base_time + timedelta(minutes=18), sender_account="ACC_MASTER_DISPERSER", receiver_account="ACC_SMURF_E4", amount=300000.0, channel=PaymentChannel.IMPS, remarks="Advisory 4"),
        Transaction(transaction_id="TXN_E_005", timestamp=base_time + timedelta(minutes=24), sender_account="ACC_MASTER_DISPERSER", receiver_account="ACC_SMURF_E5", amount=300000.0, channel=PaymentChannel.IMPS, remarks="Advisory 5"),
    ]
    return meta, accounts, transactions


def create_scenario_f_fan_in() -> Tuple[ScenarioMetadata, List[Account], List[Transaction]]:
    """Scenario F: Fan-In Funnel Aggregation."""
    base_time = datetime(2026, 9, 15, 14, 0, 0)
    meta = ScenarioMetadata(
        scenario_id="SCENARIO_F",
        title="Scenario F — Fan-In Funnel Aggregation Hub",
        description="4 feeder accounts aggregating ₹16,00,000 into a single master collection account.",
        total_volume_inr=1600000.0,
        account_count=5,
        transaction_count=4,
        primary_typology="FAN_IN",
        difficulty="MEDIUM",
    )
    accounts = [
        Account(account_id="ACC_FEEDER_F1", account_holder_name="Retail Feeder 1", account_type="SAVINGS", bank_name="HDFC Bank"),
        Account(account_id="ACC_FEEDER_F2", account_holder_name="Retail Feeder 2", account_type="SAVINGS", bank_name="ICICI Bank"),
        Account(account_id="ACC_FEEDER_F3", account_holder_name="Retail Feeder 3", account_type="SAVINGS", bank_name="Axis Bank"),
        Account(account_id="ACC_FEEDER_F4", account_holder_name="Retail Feeder 4", account_type="SAVINGS", bank_name="Kotak Bank"),
        Account(account_id="ACC_MASTER_AGGREGATOR", account_holder_name="Central Escrow Hub", account_type="CURRENT", bank_name="State Bank of India"),
    ]
    transactions = [
        Transaction(transaction_id="TXN_F_001", timestamp=base_time, sender_account="ACC_FEEDER_F1", receiver_account="ACC_MASTER_AGGREGATOR", amount=400000.0, channel=PaymentChannel.UPI, remarks="Deposit 1"),
        Transaction(transaction_id="TXN_F_002", timestamp=base_time + timedelta(minutes=10), sender_account="ACC_FEEDER_F2", receiver_account="ACC_MASTER_AGGREGATOR", amount=400000.0, channel=PaymentChannel.UPI, remarks="Deposit 2"),
        Transaction(transaction_id="TXN_F_003", timestamp=base_time + timedelta(minutes=20), sender_account="ACC_FEEDER_F3", receiver_account="ACC_MASTER_AGGREGATOR", amount=400000.0, channel=PaymentChannel.UPI, remarks="Deposit 3"),
        Transaction(transaction_id="TXN_F_004", timestamp=base_time + timedelta(minutes=30), sender_account="ACC_FEEDER_F4", receiver_account="ACC_MASTER_AGGREGATOR", amount=400000.0, channel=PaymentChannel.UPI, remarks="Deposit 4"),
    ]
    return meta, accounts, transactions


def create_scenario_g_primary() -> Tuple[ScenarioMetadata, List[Account], List[Transaction]]:
    """
    Scenario G: PRIMARY DEMONSTRATION SCENARIO — Combined Multi-Stage Laundering Network.
    Full lifecycle:
    1. INJECTION: ACC_ORIGINATOR_A injects ₹50,00,000 to ACC_GATEKEEPER_MULE.
    2. DISPERSION: Gatekeeper rapidly forwards ₹49,00,000 to ACC_DISPERSER_HUB.
       Disperser splits into 3 structured smurf accounts: ACC_SMURF_TIER1_A, ACC_SMURF_TIER1_B, ACC_SMURF_TIER1_C.
    3. LAYERING: Smurf accounts route through multi-hop transit mules (ACC_MULE_TRANSIT_X1, ACC_MULE_TRANSIT_X2).
       Includes a subtle 2-party cycle between ACC_MULE_TRANSIT_X1 and ACC_LOOP_SHELL_Y.
    4. CONVERGENCE: Transit streams converge into ACC_AGGREGATOR_X.
    5. SINK: Aggregator performs final high-value RTGS transfer of ₹46,50,000 to ACC_SINK_DEST.
    Total Volume: > ₹2,50,00,000 across multiple hops, 12 accounts, 14 transactions.
    """
    base_time = datetime(2026, 9, 15, 10, 0, 0)
    meta = ScenarioMetadata(
        scenario_id="SCENARIO_G",
        title="Scenario G — Combined Multi-Stage Laundering Network (PRIMARY DEMO)",
        description=(
            "End-to-end multi-stage syndicate incorporating Placement, Dispersion, "
            "Layering, Convergence, Rapid Forwarding, and Round-Tripping across 12 synthetic Indian accounts."
        ),
        total_volume_inr=26500000.0,
        account_count=12,
        transaction_count=14,
        primary_typology="COMBINED_MULTI_STAGE_SYNDICATE",
        difficulty="HIGH",
    )

    accounts = [
        Account(account_id="ACC_ORIGINATOR_A", account_holder_name="Nexus Prime Offshore (Originator)", account_type="CURRENT", bank_name="HDFC Bank", ifsc_code="HDFC0001099"),
        Account(account_id="ACC_GATEKEEPER_MULE", account_holder_name="Rajesh Rapid Gatekeeper Mule", account_type="SAVINGS", bank_name="State Bank of India", ifsc_code="SBIN0004211"),
        Account(account_id="ACC_DISPERSER_HUB", account_holder_name="Omicron Dispersion Enterprises", account_type="CURRENT", bank_name="ICICI Bank", ifsc_code="ICIC0009823"),
        Account(account_id="ACC_SMURF_TIER1_A", account_holder_name="Amit Smurf Tier 1", account_type="SAVINGS", bank_name="Axis Bank", ifsc_code="UTIB0002100"),
        Account(account_id="ACC_SMURF_TIER1_B", account_holder_name="Sunil Smurf Tier 2", account_type="SAVINGS", bank_name="Kotak Bank", ifsc_code="KKBK0003412"),
        Account(account_id="ACC_SMURF_TIER1_C", account_holder_name="Deepak Smurf Tier 3", account_type="SAVINGS", bank_name="Punjab National Bank", ifsc_code="PUNB0005510"),
        Account(account_id="ACC_MULE_TRANSIT_X1", account_holder_name="Apex Layering Transit A", account_type="SAVINGS", bank_name="HDFC Bank", ifsc_code="HDFC0002341"),
        Account(account_id="ACC_MULE_TRANSIT_X2", account_holder_name="Vertex Layering Transit B", account_type="SAVINGS", bank_name="ICICI Bank", ifsc_code="ICIC0001199"),
        Account(account_id="ACC_LOOP_SHELL_Y", account_holder_name="Silverline Round-Trip Shell", account_type="CURRENT", bank_name="Yes Bank", ifsc_code="YESB0008811"),
        Account(account_id="ACC_AGGREGATOR_X", account_holder_name="Global Master Aggregator", account_type="CURRENT", bank_name="State Bank of India", ifsc_code="SBIN0009988"),
        Account(account_id="ACC_SINK_DEST", account_holder_name="Horizon Capital Offshore Sink", account_type="CURRENT", bank_name="Standard Chartered", ifsc_code="SCBL0036001"),
        Account(account_id="ACC_LEGITIMATE_AUDIT", account_holder_name="Statutory Compliance Escrow", account_type="CURRENT", bank_name="HDFC Bank", ifsc_code="HDFC0005001"),
    ]

    transactions = [
        # 1. INJECTION
        Transaction(transaction_id="TXN_G_001", timestamp=base_time, sender_account="ACC_ORIGINATOR_A", receiver_account="ACC_GATEKEEPER_MULE", amount=5000000.0, channel=PaymentChannel.RTGS, remarks="Foreign Inward Remittance"),
        
        # 2. RAPID MOVEMENT / GATEKEEPER PASS-THROUGH
        Transaction(transaction_id="TXN_G_002", timestamp=base_time + timedelta(minutes=5), sender_account="ACC_GATEKEEPER_MULE", receiver_account="ACC_DISPERSER_HUB", amount=4900000.0, channel=PaymentChannel.RTGS, remarks="Contractor Forwarding"),

        # 3. DISPERSION / FAN-OUT (Split ₹49L into 3 streams: ₹17L, ₹16L, ₹16L)
        Transaction(transaction_id="TXN_G_003", timestamp=base_time + timedelta(minutes=14), sender_account="ACC_DISPERSER_HUB", receiver_account="ACC_SMURF_TIER1_A", amount=1700000.0, channel=PaymentChannel.IMPS, remarks="Advisory Retainer A"),
        Transaction(transaction_id="TXN_G_004", timestamp=base_time + timedelta(minutes=17), sender_account="ACC_DISPERSER_HUB", receiver_account="ACC_SMURF_TIER1_B", amount=1600000.0, channel=PaymentChannel.IMPS, remarks="Advisory Retainer B"),
        Transaction(transaction_id="TXN_G_005", timestamp=base_time + timedelta(minutes=20), sender_account="ACC_DISPERSER_HUB", receiver_account="ACC_SMURF_TIER1_C", amount=1600000.0, channel=PaymentChannel.IMPS, remarks="Advisory Retainer C"),

        # 4. LAYERING & TRANSIT HOPS
        Transaction(transaction_id="TXN_G_006", timestamp=base_time + timedelta(minutes=28), sender_account="ACC_SMURF_TIER1_A", receiver_account="ACC_MULE_TRANSIT_X1", amount=1650000.0, channel=PaymentChannel.IMPS, remarks="Equipment Subcontract"),
        Transaction(transaction_id="TXN_G_007", timestamp=base_time + timedelta(minutes=31), sender_account="ACC_SMURF_TIER1_B", receiver_account="ACC_MULE_TRANSIT_X1", amount=1550000.0, channel=PaymentChannel.IMPS, remarks="Logistics Subcontract"),
        Transaction(transaction_id="TXN_G_008", timestamp=base_time + timedelta(minutes=35), sender_account="ACC_SMURF_TIER1_C", receiver_account="ACC_MULE_TRANSIT_X2", amount=1580000.0, channel=PaymentChannel.IMPS, remarks="Software Consulting"),

        # 5. CIRCULAR / ROUND-TRIP SIDE LOOP
        Transaction(transaction_id="TXN_G_009", timestamp=base_time + timedelta(minutes=42), sender_account="ACC_MULE_TRANSIT_X1", receiver_account="ACC_LOOP_SHELL_Y", amount=400000.0, channel=PaymentChannel.IMPS, remarks="Short Term Liquidity"),
        Transaction(transaction_id="TXN_G_010", timestamp=base_time + timedelta(minutes=48), sender_account="ACC_LOOP_SHELL_Y", receiver_account="ACC_MULE_TRANSIT_X1", amount=390000.0, channel=PaymentChannel.IMPS, remarks="Liquidity Return"),

        # 6. CONVERGENCE / FAN-IN (Transit nodes funneling into Aggregator)
        Transaction(transaction_id="TXN_G_011", timestamp=base_time + timedelta(minutes=55), sender_account="ACC_MULE_TRANSIT_X1", receiver_account="ACC_AGGREGATOR_X", amount=3100000.0, channel=PaymentChannel.RTGS, remarks="Consolidated Settlement A"),
        Transaction(transaction_id="TXN_G_012", timestamp=base_time + timedelta(minutes=58), sender_account="ACC_MULE_TRANSIT_X2", receiver_account="ACC_AGGREGATOR_X", amount=1550000.0, channel=PaymentChannel.RTGS, remarks="Consolidated Settlement B"),

        # 7. SINK / FINAL HIGH-VALUE EXIT
        Transaction(transaction_id="TXN_G_013", timestamp=base_time + timedelta(minutes=68), sender_account="ACC_AGGREGATOR_X", receiver_account="ACC_SINK_DEST", amount=4600000.0, channel=PaymentChannel.RTGS, remarks="Offshore Escrow Settlement"),

        # 8. BENIGN CONTROL TRANSFER (To demonstrate separation of legitimate flows)
        Transaction(transaction_id="TXN_G_014", timestamp=base_time + timedelta(minutes=80), sender_account="ACC_DISPERSER_HUB", receiver_account="ACC_LEGITIMATE_AUDIT", amount=50000.0, channel=PaymentChannel.NEFT, remarks="Statutory Audit Fee"),
    ]

    return meta, accounts, transactions


def get_all_scenarios() -> Dict[str, Tuple[ScenarioMetadata, List[Account], List[Transaction]]]:
    return {
        "SCENARIO_A": create_scenario_a_normal(),
        "SCENARIO_B": create_scenario_b_layering(),
        "SCENARIO_C": create_scenario_c_circular(),
        "SCENARIO_D": create_scenario_d_rapid_movement(),
        "SCENARIO_E": create_scenario_e_fan_out(),
        "SCENARIO_F": create_scenario_f_fan_in(),
        "SCENARIO_G": create_scenario_g_primary(),
    }
