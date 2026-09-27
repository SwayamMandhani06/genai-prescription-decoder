"""
Deterministic Mock Fixtures for Phase 8: Confidence Estimation & Calibration.
Contains all 14 required evaluation scenarios specified in PLAN.md Section 17 & Phase 8:
1. Well-calibrated high-confidence prediction
2. Overconfident prediction
3. Underconfident prediction
4. Perfectly ambiguous prediction
5. Insufficient calibration data
6. Missing raw confidence
7. Calibration unavailable
8. Medicine-name confidence
9. Dosage confidence (visually grounded, uninflated by reference)
10. Frequency confidence
11. Duration confidence
12. Multiple medicines with different confidence levels
13. Conflicting extraction vs validation signals
14. Reference-supported but visually uncertain candidate

All fixtures are strictly marked as mock fixtures for engineering and continuous integration testing.
"""

from typing import Dict, Any, List
from ai.confidence.schemas import (
    RawConfidenceSignal,
    CalibratedConfidence,
    FieldConfidenceAssessment,
    MedicineIdentityConfidence,
    DosageConfidenceAssessment,
    MedicineConfidenceAssessment,
    PrescriptionConfidenceAssessment,
)


def get_case_1_well_calibrated_high_confidence() -> Dict[str, Any]:
    """1. Well-calibrated high-confidence prediction: raw score matches empirical correctness."""
    return {
        "fixture_id": "CASE-08-01-WELL-CALIBRATED-HIGH",
        "scenario": "Well-calibrated high-confidence prediction",
        "field_name": "medicine_name",
        "observed_value": "Augmentin 625 Duo",
        "raw_signal": {
            "source": "multimodal_gemini-3.8-flash",
            "raw_value": 0.95,
            "signal_type": "model_confident_visual_stroke",
            "model_version": "gemini-3.8-flash",
            "config_version": "v1.0",
        },
        "calibrated": {
            "value": 0.94,
            "calibration_method": "platt_scaling",
            "calibration_version": "1.0.0",
            "calibration_dataset_version": "1.0.0",
            "calibration_status": "calibrated",
        },
        "status": "confident",
        "visual_evidence_supported": True,
        "conflict_detected": False,
        "is_mock": True,
    }


def get_case_2_overconfident_prediction() -> Dict[str, Any]:
    """2. Overconfident prediction: model emits high score for an erroneous extraction."""
    return {
        "fixture_id": "CASE-08-02-OVERCONFIDENT",
        "scenario": "Overconfident model prediction",
        "field_name": "medicine_name",
        "observed_value": "Atenolol",
        "ground_truth_actual": "Albuterol",
        "raw_signal": {
            "source": "multimodal_gemini-3.8-flash",
            "raw_value": 0.96,
            "signal_type": "model_uncalibrated_overconfident_stroke",
            "model_version": "gemini-3.8-flash",
            "config_version": "v1.0",
        },
        "calibrated": {
            "value": 0.72,
            "calibration_method": "platt_scaling",
            "calibration_version": "1.0.0",
            "calibration_dataset_version": "1.0.0",
            "calibration_status": "calibrated",
        },
        "status": "flagged",
        "visual_evidence_supported": True,
        "conflict_detected": True,
        "conflict_description": "Overconfidence gap detected; calibrated posterior scales down uncalibrated score.",
        "is_mock": True,
    }


def get_case_3_underconfident_prediction() -> Dict[str, Any]:
    """3. Underconfident prediction: low raw model confidence despite accurate stroke representation."""
    return {
        "fixture_id": "CASE-08-03-UNDERCONFIDENT",
        "scenario": "Underconfident model prediction",
        "field_name": "medicine_name",
        "observed_value": "Paracetamol",
        "raw_signal": {
            "source": "multimodal_gemini-3.8-flash",
            "raw_value": 0.55,
            "signal_type": "model_underconfident_clean_stroke",
            "model_version": "gemini-3.8-flash",
            "config_version": "v1.0",
        },
        "calibrated": {
            "value": 0.78,
            "calibration_method": "platt_scaling",
            "calibration_version": "1.0.0",
            "calibration_dataset_version": "1.0.0",
            "calibration_status": "calibrated",
        },
        "status": "confident",
        "visual_evidence_supported": True,
        "conflict_detected": False,
        "is_mock": True,
    }


def get_case_4_perfectly_ambiguous_prediction() -> Dict[str, Any]:
    """4. Perfectly ambiguous prediction: raw score is 0.50 with competing stroke interpretations."""
    return {
        "fixture_id": "CASE-08-04-AMBIGUOUS-050",
        "scenario": "Perfect visual ambiguity (0.50 score)",
        "field_name": "medicine_name",
        "observed_value": "Ce...",
        "candidates": ["Cefixime", "Cetirizine"],
        "raw_signal": {
            "source": "multimodal_gemini-3.8-flash",
            "raw_value": 0.50,
            "signal_type": "model_ambiguous_cursive_stroke",
            "model_version": "gemini-3.8-flash",
            "config_version": "v1.0",
        },
        "calibrated": {
            "value": 0.50,
            "calibration_method": "platt_scaling",
            "calibration_version": "1.0.0",
            "calibration_dataset_version": "1.0.0",
            "calibration_status": "calibrated",
        },
        "status": "uncertain",
        "visual_evidence_supported": True,
        "conflict_detected": True,
        "conflict_description": "Equal likelihood across 2 competing clinical candidates.",
        "is_mock": True,
    }


def get_case_5_insufficient_calibration_data() -> Dict[str, Any]:
    """5. Insufficient calibration data: sample size is too small; calibration_status='insufficient_data'."""
    return {
        "fixture_id": "CASE-08-05-INSUFFICIENT-DATA",
        "scenario": "Sample size below statistical calibration threshold",
        "field_name": "medicine_name",
        "observed_value": "Amoxicillin",
        "raw_signal": {
            "source": "multimodal_gemini-3.8-flash",
            "raw_value": 0.88,
            "signal_type": "model_token_logprob_surrogate",
            "model_version": "gemini-3.8-flash",
            "config_version": "v1.0",
        },
        "calibrated": {
            "value": None,
            "calibration_method": "platt_scaling",
            "calibration_version": "1.0.0",
            "calibration_dataset_version": "1.0.0",
            "calibration_status": "insufficient_data",
        },
        "status": "confident",
        "visual_evidence_supported": True,
        "conflict_detected": False,
        "is_mock": True,
    }


def get_case_6_missing_raw_confidence() -> Dict[str, Any]:
    """6. Missing raw confidence: field is absent/missing; raw_value is None."""
    return {
        "fixture_id": "CASE-08-06-MISSING-CONFIDENCE",
        "scenario": "Absent posology field with null confidence signal",
        "field_name": "duration",
        "observed_value": None,
        "raw_signal": {
            "source": "multimodal_gemini-3.8-flash",
            "raw_value": None,
            "signal_type": "absent_field_null_signal",
            "model_version": "gemini-3.8-flash",
            "config_version": "v1.0",
        },
        "calibrated": {
            "value": None,
            "calibration_method": None,
            "calibration_version": None,
            "calibration_dataset_version": "1.0.0",
            "calibration_status": "not_available",
        },
        "status": "uncertain",
        "visual_evidence_supported": False,
        "conflict_detected": False,
        "is_mock": True,
    }


def get_case_7_calibration_unavailable() -> Dict[str, Any]:
    """7. Calibration unavailable: model provider produced no signal."""
    return {
        "fixture_id": "CASE-08-07-CALIBRATION-UNAVAILABLE",
        "scenario": "Provider emits uncalibrated discrete token without logprobs",
        "field_name": "abbreviation",
        "observed_value": "SOS",
        "raw_signal": {
            "source": "heuristics_posology_table",
            "raw_value": 0.90,
            "signal_type": "heuristic_rule_match",
            "model_version": None,
            "config_version": "v1.0",
        },
        "calibrated": {
            "value": None,
            "calibration_method": None,
            "calibration_version": None,
            "calibration_dataset_version": None,
            "calibration_status": "uncalibrated",
        },
        "status": "confident",
        "visual_evidence_supported": True,
        "conflict_detected": False,
        "is_mock": True,
    }


def get_case_8_medicine_name_confidence() -> Dict[str, Any]:
    """8. Medicine-name confidence: field-level evaluation of drug brand/generic candidate."""
    return {
        "fixture_id": "CASE-08-08-MEDICINE-NAME",
        "scenario": "Medicine name candidate evaluation",
        "field_name": "medicine_name",
        "observed_value": "Augmentin 625 Duo",
        "raw_signal": {
            "source": "multimodal_gemini-3.8-flash",
            "raw_value": 0.95,
            "signal_type": "model_confident_visual_stroke",
            "model_version": "gemini-3.8-flash",
            "config_version": "v1.0",
        },
        "calibrated": {
            "value": 0.93,
            "calibration_method": "platt_scaling",
            "calibration_version": "1.0.0",
            "calibration_dataset_version": "1.0.0",
            "calibration_status": "calibrated",
        },
        "status": "confident",
        "visual_evidence_supported": True,
        "conflict_detected": False,
        "is_mock": True,
    }


def get_case_9_dosage_confidence_visually_grounded() -> Dict[str, Any]:
    """9. Dosage confidence: grounded strictly in visual evidence, uninflated by reference formulary."""
    return {
        "fixture_id": "CASE-08-09-DOSAGE-VISUAL-GROUNDING",
        "scenario": "Dosage confidence strictly visual",
        "observed_dosage": "500 mg",
        "reference_strength": "500 mg",
        "visual_extraction_confidence": {
            "source": "multimodal_gemini-3.8-flash",
            "raw_value": 0.92,
            "signal_type": "model_confident_visual_stroke",
            "model_version": "gemini-3.8-flash",
            "config_version": "v1.0",
        },
        "reference_support_status": "matching",
        "calibrated": {
            "value": 0.89,
            "calibration_method": "platt_scaling",
            "calibration_version": "1.0.0",
            "calibration_dataset_version": "1.0.0",
            "calibration_status": "calibrated",
        },
        "explanation": "Dosage confidence is grounded strictly in visual handwriting extraction clarity (raw score: 0.92). Observed value '500 mg' is evaluated independently of reference strength '500 mg'.",
        "is_mock": True,
    }


def get_case_10_frequency_confidence() -> Dict[str, Any]:
    """10. Frequency confidence: administration schedule evaluation."""
    return {
        "fixture_id": "CASE-08-10-FREQUENCY",
        "scenario": "Frequency administration schedule evaluation",
        "field_name": "frequency",
        "observed_value": "1-0-1 (BD)",
        "raw_signal": {
            "source": "multimodal_gemini-3.8-flash",
            "raw_value": 0.94,
            "signal_type": "model_confident_visual_stroke",
            "model_version": "gemini-3.8-flash",
            "config_version": "v1.0",
        },
        "calibrated": {
            "value": 0.91,
            "calibration_method": "platt_scaling",
            "calibration_version": "1.0.0",
            "calibration_dataset_version": "1.0.0",
            "calibration_status": "calibrated",
        },
        "status": "confident",
        "visual_evidence_supported": True,
        "conflict_detected": False,
        "is_mock": True,
    }


def get_case_11_duration_confidence() -> Dict[str, Any]:
    """11. Duration confidence: treatment duration evaluation."""
    return {
        "fixture_id": "CASE-08-11-DURATION",
        "scenario": "Treatment duration evaluation",
        "field_name": "duration",
        "observed_value": "5 days",
        "raw_signal": {
            "source": "multimodal_gemini-3.8-flash",
            "raw_value": 0.92,
            "signal_type": "model_confident_visual_stroke",
            "model_version": "gemini-3.8-flash",
            "config_version": "v1.0",
        },
        "calibrated": {
            "value": 0.90,
            "calibration_method": "platt_scaling",
            "calibration_version": "1.0.0",
            "calibration_dataset_version": "1.0.0",
            "calibration_status": "calibrated",
        },
        "status": "confident",
        "visual_evidence_supported": True,
        "conflict_detected": False,
        "is_mock": True,
    }


def get_case_12_multiple_medicines_independent_confidence() -> Dict[str, Any]:
    """12. Multiple medicines: Medicine A has high confidence, Medicine B has low/uncertain confidence."""
    return {
        "fixture_id": "CASE-08-12-MULTI-MED-INDEPENDENCE",
        "scenario": "Multi-medicine independent confidence evaluation",
        "prescription_id": "TEST-RX-MULTI-MED",
        "medicines": [
            {
                "item_index": 1,
                "medicine_name": "Paracetamol",
                "overall_raw_confidence": 0.95,
                "overall_calibrated_confidence": 0.93,
                "calibration_status": "calibrated",
                "status": "confident",
            },
            {
                "item_index": 2,
                "medicine_name": "Amox...",
                "overall_raw_confidence": 0.45,
                "overall_calibrated_confidence": 0.42,
                "calibration_status": "calibrated",
                "status": "uncertain",
            },
        ],
        "is_mock": True,
    }


def get_case_13_conflicting_extraction_vs_validation() -> Dict[str, Any]:
    """13. Conflicting extraction vs validation: low visual clarity (0.45) vs high retrieval similarity (0.98)."""
    return {
        "fixture_id": "CASE-08-13-CONFLICTING-EVIDENCE",
        "scenario": "Low visual stroke confidence vs high formulary retrieval match",
        "field_name": "medicine_name",
        "observed_value": "Amox...",
        "matched_reference": "Amoxicillin 500mg",
        "visual_extraction_confidence": {
            "source": "multimodal_gemini-3.8-flash",
            "raw_value": 0.45,
            "signal_type": "model_ambiguous_cursive_stroke",
            "model_version": "gemini-3.8-flash",
            "config_version": "v1.0",
        },
        "reference_correspondence_confidence": {
            "source": "rag_cdsco-approved-drugs",
            "raw_value": 0.98,
            "signal_type": "retrieval_match_token_overlap",
            "model_version": None,
            "config_version": "v1.0",
        },
        "conflict_detected": True,
        "conflict_note": "Conflicting Evidence: Visual handwriting clarity is 0.45 while formulary retrieval similarity is 0.98 (delta: 0.53). Nomenclature match does not erase visual stroke ambiguity.",
        "is_mock": True,
    }


def get_case_14_reference_supported_visually_uncertain() -> Dict[str, Any]:
    """14. Reference-supported but visually uncertain candidate: retrieval does NOT erase visual uncertainty."""
    return {
        "fixture_id": "CASE-08-14-REFERENCE-SUPPORTED-VISUALLY-UNCERTAIN",
        "scenario": "Strong reference grounding does not erase visual handwriting ambiguity",
        "observed_candidate": "Amox...",
        "retrieved_reference": "Amoxicillin",
        "visual_status": "uncertain",
        "retrieval_status": "validated",
        "retained_uncertainty": True,
        "explanation": "Reference grounding establishes plausible nomenclature correspondence, but visual uncertainty in handwriting is strictly preserved.",
        "is_mock": True,
    }


def get_all_confidence_fixtures() -> List[Dict[str, Any]]:
    """Returns a list of all 14 deterministic Phase 8 evaluation fixtures."""
    return [
        get_case_1_well_calibrated_high_confidence(),
        get_case_2_overconfident_prediction(),
        get_case_3_underconfident_prediction(),
        get_case_4_perfectly_ambiguous_prediction(),
        get_case_5_insufficient_calibration_data(),
        get_case_6_missing_raw_confidence(),
        get_case_7_calibration_unavailable(),
        get_case_8_medicine_name_confidence(),
        get_case_9_dosage_confidence_visually_grounded(),
        get_case_10_frequency_confidence(),
        get_case_11_duration_confidence(),
        get_case_12_multiple_medicines_independent_confidence(),
        get_case_13_conflicting_extraction_vs_validation(),
        get_case_14_reference_supported_visually_uncertain(),
    ]
