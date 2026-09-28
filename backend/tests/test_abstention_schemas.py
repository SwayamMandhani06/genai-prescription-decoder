"""
Unit tests for Phase 9 Abstention and Human Verification Schemas.
Verifies:
- AbstentionReasonCode taxonomy
- FieldAbstentionDecision validation
- PrescriptionAbstentionDecision validation
- HumanVerificationRecord immutability and audit schemas
"""

import pytest
from pydantic import ValidationError
from ai.abstention.reasons import AbstentionReasonCode, get_reason_description
from ai.abstention.schemas import (
    FieldAbstentionDecision,
    FieldConfidenceMetadata,
    HumanVerificationRecord,
    PrescriptionAbstentionDecision,
    PrescriptionVerificationState,
)


class TestAbstentionSchemas:
    def test_reason_code_taxonomy(self):
        codes = [c.value for c in AbstentionReasonCode]
        assert "CALIBRATION_UNAVAILABLE" in codes
        assert "CALIBRATION_INSUFFICIENT_DATA" in codes
        assert "LOW_CALIBRATED_CONFIDENCE" in codes
        assert "EXTRACTION_UNCERTAIN" in codes
        assert "FIELD_MISSING" in codes
        assert "MULTIPLE_CANDIDATES" in codes
        assert "VISUAL_RETRIEVAL_DISCREPANCY" in codes
        assert "DOSAGE_FORMULATION_MISMATCH" in codes
        assert "AMBIGUOUS_CURSIVE_STROKE" in codes
        assert "VALIDATION_CONFLICT" in codes
        assert "UNSUPPORTED_FIELD" in codes
        assert "MODEL_OUTPUT_INCOMPLETE" in codes
        assert "PROCESSING_UNCERTAIN" in codes

        # Phase 10 introduces LASA_CONFUSION_RISK to reason codes
        assert "LASA_CONFUSION_RISK" in codes

        # Check description retrieval
        desc = get_reason_description(AbstentionReasonCode.DOSAGE_FORMULATION_MISMATCH)
        assert "dosage" in desc.lower()

    def test_field_abstention_decision_schema(self):
        decision = FieldAbstentionDecision(
            field_name="dosage",
            field_label="Dosage Strength",
            original_value="1000 mg",
            decision="abstained",
            requires_human_verification=True,
            reason_codes=["DOSAGE_FORMULATION_MISMATCH"],
            reasons_detail=["Observed dosage mismatches reference strength."],
            confidence=FieldConfidenceMetadata(
                raw_value=0.95,
                calibrated_value=None,
                calibration_status="insufficient_data",
                calibration_method=None,
            ),
            conflicts=["DOSAGE_FORMULATION_MISMATCH"],
            observed_dosage_preserved=True,
        )
        assert decision.decision == "abstained"
        assert decision.requires_human_verification is True
        assert decision.observed_dosage_preserved is True
        assert decision.confidence.calibration_status == "insufficient_data"

    def test_prescription_abstention_decision_schema(self):
        p_dec = PrescriptionAbstentionDecision(
            prescription_id="RX-TEST-001",
            policy_version="abstention_policy_v1",
            prescription_decision="REQUIRES_HUMAN_VERIFICATION",
            requires_human_verification=True,
            fields={},
            medicines=[],
            fields_requiring_verification=["dosage"],
            total_fields_evaluated=4,
            abstained_fields_count=1,
            abstention_rate=0.25,
            summary="Dosage requires verification.",
            config_hash="abc123hash",
            timestamp="2026-09-27T00:00:00Z",
        )
        assert p_dec.prescription_decision == "REQUIRES_HUMAN_VERIFICATION"
        assert p_dec.abstention_rate == 0.25

    def test_human_verification_record_schema(self):
        rec = HumanVerificationRecord(
            verification_id="VERIF-001",
            prescription_id="RX-TEST-001",
            field_id="dosage",
            original_value="1000 mg",
            verified_value="1000 mg",
            verification_status="confirmed",
            verifier_action="confirm",
            reason="Confirmed visually against script",
            timestamp="2026-09-27T00:00:00Z",
            policy_version="abstention_policy_v1",
            system_version="1.0.0",
        )
        assert rec.verification_status == "confirmed"
        assert rec.original_value == "1000 mg"
        assert rec.verified_value == "1000 mg"

    def test_invalid_decision_state_raises_validation_error(self):
        with pytest.raises(ValidationError):
            FieldAbstentionDecision(
                field_name="dosage",
                field_label="Dosage",
                decision="maybe",  # Invalid state
                requires_human_verification=True,
                confidence=FieldConfidenceMetadata(calibration_status="calibrated"),
            )
