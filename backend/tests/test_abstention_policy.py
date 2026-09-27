"""
Unit tests for Phase 9 Abstention Policy Evaluation Logic.
Verifies:
- Configurable thresholds and policy versioning
- Calibrated confidence acceptance vs low-confidence abstention
- Boundary testing around 0.80 acceptance threshold
- Conservative handling of insufficient data (N=7 real dataset)
- Uncalibrated raw score handling (no treating raw score as probability)
- Missing field handling
- Competing candidate handling
- Visual retrieval discrepancy preservation
- Dosage formulation mismatch and dosage immutability
- Multi-medicine independence and prescription-level aggregation
"""

import pytest
from backend.app.multimodal.schemas import ExtractedField, ExtractedMedicine, PrescriptionExtractionResult, ModelMetadata
from ai.rag.schemas import MedicineValidationResult, RetrievalCandidate, ValidationDecisionProvenance
from ai.rag.sources import get_source_provenance, CDSCO_SOURCE_ID
from ai.confidence.schemas import (
    FieldConfidenceAssessment,
    RawConfidenceSignal,
    CalibratedConfidence,
    DosageConfidenceAssessment,
    MedicineConfidenceAssessment,
    PrescriptionConfidenceAssessment,
)
from ai.abstention.config import AbstentionPolicyConfig, get_default_abstention_config
from ai.abstention.reasons import AbstentionReasonCode
from ai.abstention.policy import (
    evaluate_field_abstention,
    evaluate_medicine_abstention,
    evaluate_prescription_abstention,
)


class TestAbstentionPolicy:
    def test_default_config_properties(self):
        cfg = get_default_abstention_config()
        assert cfg.policy_version == "abstention_policy_v1"
        assert cfg.min_calibrated_confidence == 0.80
        assert cfg.require_calibration_for_acceptance is True
        assert cfg.dosage_strict_mode is True
        # Verify deterministic hash
        h1 = cfg.get_config_hash()
        h2 = cfg.get_config_hash()
        assert h1 == h2
        assert len(h1) == 64

    def test_high_calibrated_confidence_accepted(self):
        field = ExtractedField(
            value="Augmentin 625 Duo",
            status="confident",
            presence="present",
            extraction_state="extracted",
            confidence=0.95,
        )
        conf = FieldConfidenceAssessment(
            field_name="medicine_name",
            observed_value="Augmentin 625 Duo",
            raw_signal=RawConfidenceSignal(source="multimodal", raw_value=0.95, signal_type="model_score"),
            calibrated=CalibratedConfidence(
                value=0.92,
                calibration_method="platt_scaling",
                calibration_status="calibrated",
            ),
            status="confident",
        )
        dec = evaluate_field_abstention("medicine_name", field, conf)
        assert dec.decision == "accepted"
        assert dec.requires_human_verification is False
        assert len(dec.reason_codes) == 0

    def test_low_calibrated_confidence_abstained(self):
        field = ExtractedField(
            value="Augmentin 625 Duo",
            status="confident",
            presence="present",
            extraction_state="extracted",
            confidence=0.75,
        )
        conf = FieldConfidenceAssessment(
            field_name="medicine_name",
            observed_value="Augmentin 625 Duo",
            raw_signal=RawConfidenceSignal(source="multimodal", raw_value=0.75, signal_type="model_score"),
            calibrated=CalibratedConfidence(
                value=0.68,  # Below 0.80 threshold
                calibration_method="platt_scaling",
                calibration_status="calibrated",
            ),
            status="confident",
        )
        dec = evaluate_field_abstention("medicine_name", field, conf)
        assert dec.decision == "abstained"
        assert dec.requires_human_verification is True
        assert AbstentionReasonCode.LOW_CALIBRATED_CONFIDENCE.value in dec.reason_codes

    def test_confidence_threshold_boundary_conditions(self):
        cfg = AbstentionPolicyConfig(min_calibrated_confidence=0.80)
        field = ExtractedField(value="Amoxicillin", status="confident", presence="present", extraction_state="extracted")

        # Just below threshold (0.799)
        conf_below = FieldConfidenceAssessment(
            field_name="medicine_name",
            observed_value="Amoxicillin",
            raw_signal=RawConfidenceSignal(source="multimodal", raw_value=0.85, signal_type="model_score"),
            calibrated=CalibratedConfidence(value=0.799, calibration_status="calibrated"),
            status="confident",
        )
        dec_below = evaluate_field_abstention("medicine_name", field, conf_below, config=cfg)
        assert dec_below.decision == "abstained"

        # At/above threshold (0.800)
        conf_above = FieldConfidenceAssessment(
            field_name="medicine_name",
            observed_value="Amoxicillin",
            raw_signal=RawConfidenceSignal(source="multimodal", raw_value=0.85, signal_type="model_score"),
            calibrated=CalibratedConfidence(value=0.800, calibration_status="calibrated"),
            status="confident",
        )
        dec_above = evaluate_field_abstention("medicine_name", field, conf_above, config=cfg)
        assert dec_above.decision == "accepted"

    def test_insufficient_calibration_data_conservative_abstention(self):
        """
        N=7 real curated dataset behavior: calibration_status = 'insufficient_data'.
        System must conservatively abstain and NOT treat raw_confidence as probability.
        """
        field = ExtractedField(
            value="Augmentin 625 Duo",
            status="confident",
            presence="present",
            extraction_state="extracted",
            confidence=0.98,  # High raw score
        )
        conf = FieldConfidenceAssessment(
            field_name="medicine_name",
            observed_value="Augmentin 625 Duo",
            raw_signal=RawConfidenceSignal(source="multimodal", raw_value=0.98, signal_type="model_score"),
            calibrated=CalibratedConfidence(
                value=None,
                calibration_status="insufficient_data",
            ),
            status="confident",
        )
        dec = evaluate_field_abstention("medicine_name", field, conf)
        assert dec.decision == "abstained"
        assert dec.requires_human_verification is True
        assert AbstentionReasonCode.CALIBRATION_INSUFFICIENT_DATA.value in dec.reason_codes

    def test_uncalibrated_raw_signal_abstention(self):
        field = ExtractedField(value="Paracetamol", status="confident", presence="present", extraction_state="extracted")
        conf = FieldConfidenceAssessment(
            field_name="medicine_name",
            observed_value="Paracetamol",
            raw_signal=RawConfidenceSignal(source="multimodal", raw_value=0.90, signal_type="model_score"),
            calibrated=CalibratedConfidence(value=None, calibration_status="uncalibrated"),
            status="confident",
        )
        dec = evaluate_field_abstention("medicine_name", field, conf)
        assert dec.decision == "abstained"
        assert AbstentionReasonCode.CALIBRATION_UNAVAILABLE.value in dec.reason_codes

    def test_missing_field_abstention(self):
        field_absent = ExtractedField(
            value=None,
            status="uncertain",
            presence="absent",
            extraction_state="missing",
        )
        dec = evaluate_field_abstention("duration", field_absent)
        assert dec.decision == "abstained"
        assert dec.requires_human_verification is True
        assert AbstentionReasonCode.FIELD_MISSING.value in dec.reason_codes

    def test_uncertain_extraction_and_cursive_stroke(self):
        field_ambiguous = ExtractedField(
            value="Amox...",
            status="uncertain",
            presence="present",
            extraction_state="ambiguous",
            uncertainty_reason="Ambiguous cursive descender ligature",
            candidates=["Amoxicillin", "Ampicillin"],
        )
        dec = evaluate_field_abstention("medicine_name", field_ambiguous)
        assert dec.decision == "abstained"
        assert AbstentionReasonCode.EXTRACTION_UNCERTAIN.value in dec.reason_codes
        assert AbstentionReasonCode.AMBIGUOUS_CURSIVE_STROKE.value in dec.reason_codes
        assert AbstentionReasonCode.MULTIPLE_CANDIDATES.value in dec.reason_codes

    def test_visual_retrieval_discrepancy_abstention(self):
        field = ExtractedField(value="Amox...", status="uncertain", presence="present", extraction_state="ambiguous")
        conf = FieldConfidenceAssessment(
            field_name="medicine_name",
            observed_value="Amox...",
            raw_signal=RawConfidenceSignal(source="multimodal", raw_value=0.50, signal_type="model_score"),
            calibrated=CalibratedConfidence(value=None, calibration_status="insufficient_data"),
            status="uncertain",
            conflict_detected=True,
            conflict_description="Low visual extraction (0.50) vs high retrieval (0.98)",
        )
        dec = evaluate_field_abstention("medicine_name", field, conf)
        assert dec.decision == "abstained"
        assert AbstentionReasonCode.VISUAL_RETRIEVAL_DISCREPANCY.value in dec.reason_codes
        assert "VISUAL_RETRIEVAL_DISCREPANCY" in dec.conflicts

    def test_dosage_formulation_mismatch_and_immutability(self):
        dosage_field = ExtractedField(
            value="1000 mg",
            status="confident",
            presence="present",
            extraction_state="extracted",
            confidence=0.95,
        )
        val_res = MedicineValidationResult(
            input_candidate="Augmentin",
            normalized_candidate="augmentin",
            validation_status="uncertain",
            medicine_identity_status="validated",
            evidence="Dosage strength mismatch",
            observed_dosage="1000 mg",
            reference_strength="625 mg",
            formulation_consistency="mismatch",
            dosage_observation_preserved=True,
            requires_human_review=True,
            provenance=ValidationDecisionProvenance(
                retrieval_method="exact_normalized_name",
                query_raw="Augmentin",
                query_normalized="augmentin",
                normalization_version="v1.0",
                index_version="v1.0",
                config_hash="abc",
                matched_count=1,
                timestamp="2026-09-27T00:00:00Z",
                validation_rule="FORMULATION_MISMATCH_GATE",
                source_authorities=["cdsco"],
            )
        )
        dec = evaluate_field_abstention("dosage", dosage_field, validation_result=val_res)
        assert dec.decision == "abstained"
        assert dec.requires_human_verification is True
        assert dec.observed_dosage_preserved is True
        assert dec.original_value == "1000 mg"
        assert AbstentionReasonCode.DOSAGE_FORMULATION_MISMATCH.value in dec.reason_codes

    def test_multi_medicine_mixed_decisions_and_independence(self):
        med1 = ExtractedMedicine(
            medicine_name=ExtractedField(value="Augmentin 625 Duo", status="confident", presence="present", extraction_state="extracted"),
            dosage=ExtractedField(value="625 mg", status="confident", presence="present", extraction_state="extracted"),
            frequency=ExtractedField(value="1-0-1", status="confident", presence="present", extraction_state="extracted"),
            duration=ExtractedField(value="5 days", status="confident", presence="present", extraction_state="extracted"),
        )
        med2 = ExtractedMedicine(
            medicine_name=ExtractedField(value="Amox...", status="uncertain", presence="present", extraction_state="ambiguous"),
            dosage=ExtractedField(value="500 mg", status="confident", presence="present", extraction_state="extracted"),
            frequency=ExtractedField(value="1-0-1", status="confident", presence="present", extraction_state="extracted"),
            duration=ExtractedField(value="5 days", status="confident", presence="present", extraction_state="extracted"),
        )
        result = PrescriptionExtractionResult(
            prescription_id="RX-MULTI-01",
            original_image_url="/uploads/rx-multi-01.png",
            source_image_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            medicines=[med1, med2],
            model=ModelMetadata(
                provider="mock",
                model_id="mock-gemini-flash",
                model_version="1.0",
                prompt_version="1.0",
                config_version="1.0",
                is_mock=True,
            ),
            duration_seconds=1.2,
        )
        presc_dec = evaluate_prescription_abstention(
            prescription_id="RX-MULTI-01",
            extraction_result=result,
        )
        assert presc_dec.prescription_decision == "REQUIRES_HUMAN_VERIFICATION"
        assert presc_dec.requires_human_verification is True
        assert len(presc_dec.medicines) == 2
        assert presc_dec.medicines[1].decision == "abstained"
