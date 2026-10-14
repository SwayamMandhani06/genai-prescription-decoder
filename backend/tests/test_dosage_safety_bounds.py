"""
Unit Regression Suite for Clinical Dosage-Strength and Overdose Bounds (HIGH-04 / FMEA-01)
Verifies:
1. Exact match between observed strength and reference (e.g. 500 mg vs 500 mg) is consistent
2. Extreme magnitude / 10x overdose hazard (e.g. 5000 mg vs 500 mg) triggers mismatch and clinical alert
3. Unit confusion hazard (e.g. mg prescribed instead of mcg) triggers critical safety mismatch
"""

import pytest
from ai.rag.validator import evaluate_formulation_consistency, parse_strength_value_unit


def test_parse_strength_value_unit():
    val, unit = parse_strength_value_unit("500 mg")
    assert val == 500.0
    assert unit == "mg"

    val, unit = parse_strength_value_unit("0.25mg")
    assert val == 0.25
    assert unit == "mg"

    val, unit = parse_strength_value_unit("50 mcg")
    assert val == 50.0
    assert unit == "mcg"


def test_consistent_dosage():
    status, note = evaluate_formulation_consistency("500 mg", "500 mg")
    assert status == "consistent"

    status, note = evaluate_formulation_consistency("625 mg", "625 mg Tablet")
    assert status == "consistent"


def test_extreme_overdose_detection():
    # 5000 mg vs 500 mg reference
    status, note = evaluate_formulation_consistency("5000 mg", "500 mg")
    assert status == "mismatch"
    assert "CRITICAL_DOSAGE_OUT_OF_RANGE" in note
    assert "overdose hazard" in note.lower() or "decimal" in note.lower()


def test_unit_confusion_overdose_detection():
    # 50 mg vs 50 mcg reference (1000x overdose)
    status, note = evaluate_formulation_consistency("50 mg", "50 mcg")
    assert status == "mismatch"
    assert "CRITICAL_DOSAGE_OUT_OF_RANGE" in note
    assert "microgram" in note.lower()
