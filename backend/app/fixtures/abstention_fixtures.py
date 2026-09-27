"""
Phase 9 Deterministic Mock Fixtures: Abstention & Human Verification Scenarios.
Adheres strictly to Phase 9 specification:
- 15 deterministic test scenarios.
- All fixtures explicitly marked is_mock = True.
- Validates field-level decisions, reason codes, dosage immutability,
  and human verification actions (confirm, correct, mark_unreadable).
"""

from typing import Dict, List, Any


ABSTENTION_FIXTURES: Dict[str, Dict[str, Any]] = {
    # --------------------------------------------------------------------------
    # Scenario 1: High Confidence Accept
    # --------------------------------------------------------------------------
    "CASE-09-01-HIGH-CONFIDENCE-ACCEPT": {
        "fixture_id": "CASE-09-01-HIGH-CONFIDENCE-ACCEPT",
        "description": "High calibrated confidence (0.94 >= 0.80) with exact CDSCO grounding and no conflicts.",
        "is_mock": True,
        "input_field": {
            "field_name": "medicine_name",
            "value": "Augmentin 625 Duo",
            "status": "confident",
            "presence": "present",
            "extraction_state": "extracted",
            "confidence": 0.95,
        },
        "confidence_metadata": {
            "raw_value": 0.95,
            "calibrated_value": 0.94,
            "calibration_status": "calibrated",
            "calibration_method": "platt_scaling",
        },
        "validation_evidence": {
            "found_in_db": True,
            "validation_status": "validated",
            "matched_name": "Augmentin 625 Duo",
            "score": 1.0,
            "formulation_consistency": "consistent",
        },
        "expected_decision": {
            "decision": "accepted",
            "requires_human_verification": False,
            "reason_codes": [],
            "conflicts": [],
        }
    },

    # --------------------------------------------------------------------------
    # Scenario 2: Low Calibrated Confidence Abstain
    # --------------------------------------------------------------------------
    "CASE-09-02-LOW-CONFIDENCE-ABSTAIN": {
        "fixture_id": "CASE-09-02-LOW-CONFIDENCE-ABSTAIN",
        "description": "Calibrated confidence (0.65) falls below policy threshold (0.80).",
        "is_mock": True,
        "input_field": {
            "field_name": "frequency",
            "value": "1-0-1",
            "status": "confident",
            "presence": "present",
            "extraction_state": "extracted",
            "confidence": 0.70,
        },
        "confidence_metadata": {
            "raw_value": 0.70,
            "calibrated_value": 0.65,
            "calibration_status": "calibrated",
            "calibration_method": "platt_scaling",
        },
        "expected_decision": {
            "decision": "abstained",
            "requires_human_verification": True,
            "reason_codes": ["LOW_CALIBRATED_CONFIDENCE"],
        }
    },

    # --------------------------------------------------------------------------
    # Scenario 3: Calibration Insufficient Data (Real N=7 Cohort)
    # --------------------------------------------------------------------------
    "CASE-09-03-CALIBRATION-INSUFFICIENT": {
        "fixture_id": "CASE-09-03-CALIBRATION-INSUFFICIENT",
        "description": "Sample size is insufficient (N=7 < 15); system conservatively abstains.",
        "is_mock": True,
        "input_field": {
            "field_name": "medicine_name",
            "value": "Paracetamol 500mg",
            "status": "confident",
            "presence": "present",
            "extraction_state": "extracted",
            "confidence": 0.94,
        },
        "confidence_metadata": {
            "raw_value": 0.94,
            "calibrated_value": None,
            "calibration_status": "insufficient_data",
            "calibration_method": None,
        },
        "expected_decision": {
            "decision": "abstained",
            "requires_human_verification": True,
            "reason_codes": ["CALIBRATION_INSUFFICIENT_DATA"],
        }
    },

    # --------------------------------------------------------------------------
    # Scenario 4: Calibration Unavailable
    # --------------------------------------------------------------------------
    "CASE-09-04-CALIBRATION-UNAVAILABLE": {
        "fixture_id": "CASE-09-04-CALIBRATION-UNAVAILABLE",
        "description": "Raw model signal present but calibration unperformed; raw score is not treated as probability.",
        "is_mock": True,
        "input_field": {
            "field_name": "duration",
            "value": "5 days",
            "status": "confident",
            "presence": "present",
            "extraction_state": "extracted",
            "confidence": 0.88,
        },
        "confidence_metadata": {
            "raw_value": 0.88,
            "calibrated_value": None,
            "calibration_status": "uncalibrated",
            "calibration_method": None,
        },
        "expected_decision": {
            "decision": "abstained",
            "requires_human_verification": True,
            "reason_codes": ["CALIBRATION_UNAVAILABLE"],
        }
    },

    # --------------------------------------------------------------------------
    # Scenario 5: Uncertain Extraction
    # --------------------------------------------------------------------------
    "CASE-09-05-UNCERTAIN-EXTRACTION": {
        "fixture_id": "CASE-09-05-UNCERTAIN-EXTRACTION",
        "description": "Visual extraction status is uncertain; mandates human verification.",
        "is_mock": True,
        "input_field": {
            "field_name": "medicine_name",
            "value": "Amox...",
            "status": "uncertain",
            "presence": "present",
            "extraction_state": "ambiguous",
            "confidence": 0.50,
            "uncertainty_reason": "Degraded pen stroke obscures final syllable",
        },
        "confidence_metadata": {
            "raw_value": 0.50,
            "calibrated_value": None,
            "calibration_status": "insufficient_data",
        },
        "expected_decision": {
            "decision": "abstained",
            "requires_human_verification": True,
            "reason_codes": ["EXTRACTION_UNCERTAIN", "AMBIGUOUS_CURSIVE_STROKE", "CALIBRATION_INSUFFICIENT_DATA"],
        }
    },

    # --------------------------------------------------------------------------
    # Scenario 6: Missing Field
    # --------------------------------------------------------------------------
    "CASE-09-06-MISSING-FIELD": {
        "fixture_id": "CASE-09-06-MISSING-FIELD",
        "description": "Field absent from prescription document; abstained with FIELD_MISSING.",
        "is_mock": True,
        "input_field": {
            "field_name": "dosage",
            "value": None,
            "status": "uncertain",
            "presence": "absent",
            "extraction_state": "missing",
            "confidence": None,
        },
        "confidence_metadata": {
            "raw_value": None,
            "calibrated_value": None,
            "calibration_status": "not_available",
        },
        "expected_decision": {
            "decision": "abstained",
            "requires_human_verification": True,
            "reason_codes": ["FIELD_MISSING"],
        }
    },

    # --------------------------------------------------------------------------
    # Scenario 7: Multiple Candidates
    # --------------------------------------------------------------------------
    "CASE-09-07-MULTIPLE-CANDIDATES": {
        "fixture_id": "CASE-09-07-MULTIPLE-CANDIDATES",
        "description": "Multiple competing candidates detected; system refrains from silent guessing.",
        "is_mock": True,
        "input_field": {
            "field_name": "medicine_name",
            "value": "Amox...",
            "status": "uncertain",
            "presence": "present",
            "extraction_state": "ambiguous",
            "candidates": ["Amoxicillin", "Ampicillin"],
            "confidence": 0.55,
        },
        "confidence_metadata": {
            "raw_value": 0.55,
            "calibrated_value": None,
            "calibration_status": "insufficient_data",
        },
        "expected_decision": {
            "decision": "abstained",
            "requires_human_verification": True,
            "reason_codes": ["EXTRACTION_UNCERTAIN", "MULTIPLE_CANDIDATES"],
        }
    },

    # --------------------------------------------------------------------------
    # Scenario 8: Visual Retrieval Conflict
    # --------------------------------------------------------------------------
    "CASE-09-08-VISUAL-RETRIEVAL-CONFLICT": {
        "fixture_id": "CASE-09-08-VISUAL-RETRIEVAL-CONFLICT",
        "description": "Low visual score (0.50) with high reference match (0.98); strong retrieval cannot erase visual doubt.",
        "is_mock": True,
        "input_field": {
            "field_name": "medicine_name",
            "value": "Amox...",
            "status": "uncertain",
            "presence": "present",
            "extraction_state": "ambiguous",
            "confidence": 0.50,
        },
        "confidence_metadata": {
            "raw_value": 0.50,
            "calibrated_value": None,
            "calibration_status": "insufficient_data",
            "conflict_detected": True,
            "conflict_description": "Conflicting Evidence: Low visual extraction certainty (0.50) with high reference match (0.98)",
        },
        "expected_decision": {
            "decision": "abstained",
            "requires_human_verification": True,
            "reason_codes": ["EXTRACTION_UNCERTAIN", "VISUAL_RETRIEVAL_DISCREPANCY"],
            "conflicts": ["VISUAL_RETRIEVAL_DISCREPANCY"],
        }
    },

    # --------------------------------------------------------------------------
    # Scenario 9: Dosage Formulation Mismatch
    # --------------------------------------------------------------------------
    "CASE-09-09-DOSAGE-FORMULATION-MISMATCH": {
        "fixture_id": "CASE-09-09-DOSAGE-FORMULATION-MISMATCH",
        "description": "Prescribed 1000 mg differs from approved 625 mg; observed dosage preserved and abstained.",
        "is_mock": True,
        "input_field": {
            "field_name": "dosage",
            "value": "1000 mg",
            "status": "confident",
            "presence": "present",
            "extraction_state": "extracted",
            "confidence": 0.95,
        },
        "validation_evidence": {
            "observed_dosage": "1000 mg",
            "reference_strength": "625 mg",
            "formulation_consistency": "mismatch",
        },
        "confidence_metadata": {
            "raw_value": 0.95,
            "calibrated_value": None,
            "calibration_status": "insufficient_data",
        },
        "expected_decision": {
            "decision": "abstained",
            "requires_human_verification": True,
            "observed_dosage_preserved": True,
            "reason_codes": ["DOSAGE_FORMULATION_MISMATCH"],
            "conflicts": ["DOSAGE_FORMULATION_MISMATCH"],
        }
    },

    # --------------------------------------------------------------------------
    # Scenario 10: Ambiguous Cursive Stroke
    # --------------------------------------------------------------------------
    "CASE-09-10-AMBIGUOUS-CURSIVE": {
        "fixture_id": "CASE-09-10-AMBIGUOUS-CURSIVE",
        "description": "Cursive ligature ambiguity explicitly flagged for reviewer inspection.",
        "is_mock": True,
        "input_field": {
            "field_name": "medicine_name",
            "value": "Ce...",
            "status": "uncertain",
            "presence": "present",
            "extraction_state": "ambiguous",
            "confidence": 0.48,
            "uncertainty_reason": "Degraded cursive stroke loop with ambiguous descender",
        },
        "confidence_metadata": {
            "raw_value": 0.48,
            "calibrated_value": None,
            "calibration_status": "insufficient_data",
        },
        "expected_decision": {
            "decision": "abstained",
            "requires_human_verification": True,
            "reason_codes": ["EXTRACTION_UNCERTAIN", "AMBIGUOUS_CURSIVE_STROKE"],
        }
    },

    # --------------------------------------------------------------------------
    # Scenario 11: Multi-Medicine Mixed Decisions
    # --------------------------------------------------------------------------
    "CASE-09-11-MULTI-MEDICINE-MIXED-DECISIONS": {
        "fixture_id": "CASE-09-11-MULTI-MEDICINE-MIXED-DECISIONS",
        "description": "Med 1 accepted; Med 2 abstained. Top-level status requires human verification.",
        "is_mock": True,
        "medicines": [
            {
                "item_index": 1,
                "name": "Augmentin 625 Duo",
                "decision": "accepted",
                "requires_verification": False,
            },
            {
                "item_index": 2,
                "name": "Amox...",
                "decision": "abstained",
                "requires_verification": True,
                "reason_codes": ["EXTRACTION_UNCERTAIN", "AMBIGUOUS_CURSIVE_STROKE"],
            }
        ],
        "expected_prescription_decision": "REQUIRES_HUMAN_VERIFICATION",
        "expected_requires_human_verification": True,
    },

    # --------------------------------------------------------------------------
    # Scenario 12: Human Confirmation Action
    # --------------------------------------------------------------------------
    "CASE-09-12-HUMAN-CONFIRMATION": {
        "fixture_id": "CASE-09-12-HUMAN-CONFIRMATION",
        "description": "Human verifier confirms extracted text matches visual handwriting.",
        "is_mock": True,
        "action_request": {
            "prescription_id": "RX-DEMO-001",
            "field_id": "medicine_name",
            "action": "confirm",
            "original_value": "Augmentin 625 Duo",
            "reason": "Confirmed against handwritten document.",
        },
        "expected_record": {
            "verification_status": "confirmed",
            "verifier_action": "confirm",
            "original_value": "Augmentin 625 Duo",
            "verified_value": "Augmentin 625 Duo",
        }
    },

    # --------------------------------------------------------------------------
    # Scenario 13: Human Correction Action
    # --------------------------------------------------------------------------
    "CASE-09-13-HUMAN-CORRECTION": {
        "fixture_id": "CASE-09-13-HUMAN-CORRECTION",
        "description": "Human verifier corrects misread text; audit trail preserves original.",
        "is_mock": True,
        "action_request": {
            "prescription_id": "RX-DEMO-002",
            "field_id": "medicine_name",
            "action": "correct",
            "original_value": "Amoxcillin",
            "verified_value": "Amoxicillin",
            "reason": "Corrected minor typographical stroke error.",
        },
        "expected_record": {
            "verification_status": "corrected",
            "verifier_action": "correct",
            "original_value": "Amoxcillin",
            "verified_value": "Amoxicillin",
        }
    },

    # --------------------------------------------------------------------------
    # Scenario 14: Human Marked Unreadable Action
    # --------------------------------------------------------------------------
    "CASE-09-14-HUMAN-MARKED-UNREADABLE": {
        "fixture_id": "CASE-09-14-HUMAN-MARKED-UNREADABLE",
        "description": "Human verifier marks illegible cursive handwriting as unreadable.",
        "is_mock": True,
        "action_request": {
            "prescription_id": "RX-DEMO-003",
            "field_id": "frequency",
            "action": "mark_unreadable",
            "original_value": "???",
            "reason": "Optical stroke degradation makes schedule illegible.",
        },
        "expected_record": {
            "verification_status": "unreadable",
            "verifier_action": "mark_unreadable",
            "original_value": "???",
            "verified_value": None,
        }
    },

    # --------------------------------------------------------------------------
    # Scenario 15: Full Prescription Requires Verification
    # --------------------------------------------------------------------------
    "CASE-09-15-FULL-PRESCRIPTION-REQUIRES-VERIFICATION": {
        "fixture_id": "CASE-09-15-FULL-PRESCRIPTION-REQUIRES-VERIFICATION",
        "description": "Comprehensive prescription with mixed fields; 2 of 4 abstained.",
        "is_mock": True,
        "prescription_id": "RX-DEMO-COMPREHENSIVE",
        "total_fields": 4,
        "abstained_fields": 2,
        "expected_prescription_decision": "REQUIRES_HUMAN_VERIFICATION",
        "expected_abstention_rate": 0.50,
        "requires_human_verification": True,
    }
}


def get_abstention_fixture(fixture_id: str) -> Dict[str, Any]:
    """Retrieves a deterministic Phase 9 test fixture by ID."""
    if fixture_id not in ABSTENTION_FIXTURES:
        raise KeyError(f"Unknown Phase 9 fixture: {fixture_id}")
    return ABSTENTION_FIXTURES[fixture_id]


def list_abstention_fixtures() -> List[Dict[str, Any]]:
    """Returns all 15 deterministic Phase 9 evaluation fixtures."""
    return list(ABSTENTION_FIXTURES.values())
