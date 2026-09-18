"""
Automated tests for AML Detection Engines:
- LayeringDetector (Multi-hop sequential movement)
- CircularTransferDetector (Cycles / round-tripping)
- RapidMovementDetector (Mule velocity & dwell time)
- FanPatternsDetector (Fan-In aggregation and Fan-Out dispersion)
"""
from datetime import datetime, timedelta
import pytest
from backend.models.transaction import Transaction, PaymentChannel
from backend.graph.financial_graph import FinancialMultiGraph
from backend.detectors.layering_detector import LayeringDetector
from backend.detectors.circular_detector import CircularTransferDetector
from backend.detectors.rapid_movement_detector import RapidMovementDetector
from backend.detectors.fan_patterns_detector import FanPatternsDetector
from backend.data.scenarios import (
    create_scenario_b_layering,
    create_scenario_c_circular,
    create_scenario_d_rapid_movement,
    create_scenario_e_fan_out,
    create_scenario_f_fan_in,
)


def test_layering_detection():
    meta, accounts, txs = create_scenario_b_layering()
    g = FinancialMultiGraph()
    g.load_transactions(txs, accounts)

    detector = LayeringDetector(min_hops=3)
    findings = detector.detect(g)

    assert len(findings) >= 1
    finding = findings[0]
    assert finding.pattern_type.value == "LAYERING"
    assert finding.metrics["hop_count"] >= 3
    assert len(finding.evidence) >= 1
    assert finding.evidence[0].retention_percentage > 80.0


def test_circular_detection():
    meta, accounts, txs = create_scenario_c_circular()
    g = FinancialMultiGraph()
    g.load_transactions(txs, accounts)

    detector = CircularTransferDetector()
    findings = detector.detect(g)

    assert len(findings) >= 1
    finding = findings[0]
    assert finding.pattern_type.value == "CIRCULAR_TRANSFER"
    assert len(finding.accounts_involved) == 3
    assert finding.confidence_score > 0.85


def test_rapid_movement_detection():
    meta, accounts, txs = create_scenario_d_rapid_movement()
    g = FinancialMultiGraph()
    g.load_transactions(txs, accounts)

    detector = RapidMovementDetector(max_dwell_minutes=15.0)
    findings = detector.detect(g)

    assert len(findings) >= 1
    finding = findings[0]
    assert finding.pattern_type.value == "RAPID_MOVEMENT"
    assert finding.metrics["dwell_time_minutes"] <= 5.0
    assert finding.metrics["mule_account"] == "ACC_RAPID_MULE_D"


def test_fan_out_detection():
    meta, accounts, txs = create_scenario_e_fan_out()
    g = FinancialMultiGraph()
    g.load_transactions(txs, accounts)

    detector = FanPatternsDetector(min_fan_count=3)
    findings = detector.detect_fan_out(g)

    assert len(findings) >= 1
    finding = findings[0]
    assert finding.pattern_type.value == "FAN_OUT"
    assert finding.metrics["disperser_account"] == "ACC_MASTER_DISPERSER"
    assert finding.metrics["beneficiary_count"] == 5


def test_fan_in_detection():
    meta, accounts, txs = create_scenario_f_fan_in()
    g = FinancialMultiGraph()
    g.load_transactions(txs, accounts)

    detector = FanPatternsDetector(min_fan_count=3)
    findings = detector.detect_fan_in(g)

    assert len(findings) >= 1
    finding = findings[0]
    assert finding.pattern_type.value == "FAN_IN"
    assert finding.metrics["aggregator_account"] == "ACC_MASTER_AGGREGATOR"
    assert finding.metrics["feeder_count"] == 4
