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


@pytest.mark.parametrize("ep_status,val,expected_decision", [
    ("EXTRACTED", "500 mg", "accepted"),
    ("MISSING_ON_RX", None, "abstained"),
    ("ILLEGIBLE", "[?] mg", "abstained"),
    ("AMBIGUOUS", "250 or 500 mg", "abstained"),
    ("UNVERIFIED", "99999 mg", "abstained"),
])
def test_dosage_field_epistemic_statuses(ep_status, val, expected_decision):
    from backend.app.multimodal.schemas import ExtractedField
    from ai.abstention.policy import evaluate_field_abstention
    from ai.confidence.schemas import FieldConfidenceAssessment, RawConfidenceSignal, CalibratedConfidence

    field = ExtractedField(
        value=val,
        status="confident" if ep_status == "EXTRACTED" else "uncertain",
        presence="absent" if ep_status == "MISSING_ON_RX" else "present",
        extraction_state="missing" if ep_status == "MISSING_ON_RX" else ("extracted" if ep_status == "EXTRACTED" else "ambiguous"),
        epistemic_status=ep_status,
    )
    conf = None
    if ep_status == "EXTRACTED":
        conf = FieldConfidenceAssessment(
            field_name="dosage",
            observed_value=val,
            raw_signal=RawConfidenceSignal(source="multimodal", raw_value=0.95, signal_type="model_score"),
            calibrated=CalibratedConfidence(value=0.92, calibration_status="calibrated"),
            status="confident",
        )
    dec = evaluate_field_abstention("dosage", field, conf)
    assert dec.decision == expected_decision
    assert dec.epistemic_status == ep_status
    if expected_decision == "abstained":
        assert dec.requires_pharmacist_verification is True
    else:
        assert dec.requires_pharmacist_verification is False


def test_dosage_decimal_blur_hazard_mandates_pharmacist_verification():
    from backend.app.multimodal.schemas import ExtractedField
    from ai.abstention.policy import evaluate_field_abstention
    from ai.abstention.reasons import AbstentionReasonCode

    # 0.5 mg on a blurred image is a critical clinical hazard (0.5 vs 5 vs 50)
    field = ExtractedField(
        value="0.5 mg",
        status="confident",
        presence="present",
        extraction_state="extracted",
    )
    dec = evaluate_field_abstention(
        "dosage",
        field,
        image_quality_flags={"blur_detected": True},
    )
    assert dec.decision == "abstained"
    assert dec.requires_pharmacist_verification is True
    assert AbstentionReasonCode.DECIMAL_BLUR_HAZARD.value in dec.reason_codes

