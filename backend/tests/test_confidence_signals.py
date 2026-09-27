"""
Unit tests for Phase 8 Confidence Signal Extraction and Conflict Detection.
Verifies:
- Extraction of raw signals from ExtractedField
- Strict visual grounding of dosage confidence
- Separation of visual extraction from retrieval similarity
- Conflict detection and preservation
"""

import pytest
from backend.app.multimodal.schemas import ExtractedField, ExtractedMedicine
from ai.rag.schemas import MedicineValidationResult, RetrievalCandidate, ValidationDecisionProvenance
from ai.rag.sources import get_source_provenance, CDSCO_SOURCE_ID
from ai.confidence.signals import (
    extract_field_confidence_signal,
    extract_dosage_confidence_signal,
    extract_medicine_identity_confidence,
    detect_confidence_conflicts,
)


class TestConfidenceSignals:
    def test_extract_field_signal_confident(self):
        field = ExtractedField(
            value="Augmentin 625 Duo",
            status="confident",
            presence="present",
            extraction_state="extracted",
        )
        sig = extract_field_confidence_signal(field, "medicine_name")
        assert sig.raw_value == 0.95
        assert "confident" in sig.signal_type

    def test_extract_field_signal_ambiguous(self):
        field = ExtractedField(
            value="Amox...",
            status="uncertain",
            presence="present",
            extraction_state="ambiguous",
            candidates=["Amoxicillin", "Amikacin"],
        )
        sig = extract_field_confidence_signal(field, "medicine_name")
        assert sig.raw_value == 0.50
        assert "ambiguous" in sig.signal_type

    def test_extract_field_signal_absent_null(self):
        field = ExtractedField(
            value=None,
            status="uncertain",
            presence="absent",
            extraction_state="missing",
        )
        sig = extract_field_confidence_signal(field, "duration")
        assert sig.raw_value is None
        assert "absent" in sig.signal_type

    def test_dosage_confidence_strictly_visual_and_detects_mismatch(self):
        dosage_field = ExtractedField(
            value="1000 mg",
            status="confident",
            presence="present",
            extraction_state="extracted",
        )
        ref_cand = RetrievalCandidate(
            reference_id="REF-CDSCO-001",
            source="cdsco-approved-drugs",
            medicine_name="Augmentin 625 Duo",
            score=1.0,
            match_method="exact_normalized_name",
            strength="625 mg",
            evidence="Exact match in CDSCO",
            provenance=get_source_provenance(CDSCO_SOURCE_ID),
        )
        val_res = MedicineValidationResult(
            input_candidate="Augmentin 625 Duo",
            normalized_candidate="augmentin 625 duo",
            validation_status="validated",
            medicine_identity_status="validated",
            selected_reference=ref_cand,
            evidence="Exact match in CDSCO",
            requires_human_review=True,
            dosage_observation_preserved=True,
            observed_dosage="1000 mg",
            reference_strength="625 mg",
            formulation_consistency="mismatch",
            provenance=ValidationDecisionProvenance(
                retrieval_method="exact_name",
                query_raw="Augmentin 625 Duo",
                query_normalized="augmentin 625 duo",
                normalization_version="v1.0",
                index_version="v1.0",
                config_hash="abc",
                matched_count=1,
                timestamp="2026-09-27T00:00:00Z",
                validation_rule="HIGH_CONFIDENCE_FORMULARY_VALIDATED",
                source_authorities=["cdsco"],
            )
        )
        dosage_assessment = extract_dosage_confidence_signal(dosage_field, val_res)
        assert dosage_assessment.observed_dosage == "1000 mg"
        assert dosage_assessment.reference_strength == "625 mg"
        assert dosage_assessment.reference_support_status == "mismatch"
        assert "mismatch" in dosage_assessment.explanation.lower()
        # Visual extraction raw confidence is preserved without mutation
        assert dosage_assessment.visual_extraction_confidence.raw_value == 0.95

    def test_medicine_identity_conflict_detection(self):
        # Case: Cursive truncated stroke ("Amox...") has low visual confidence (0.50),
        # but retrieval finds "Amoxicillin" with score 0.98
        name_field = ExtractedField(
            value="Amox...",
            status="uncertain",
            presence="present",
            extraction_state="ambiguous",
            candidates=["Amoxicillin", "Amikacin"],
        )
        ref_cand = RetrievalCandidate(
            reference_id="REF-CDSCO-002",
            source="cdsco-approved-drugs",
            medicine_name="Amoxicillin 500mg",
            score=0.98,
            match_method="token_overlap",
            strength="500 mg",
            evidence="Token overlap match",
            provenance=get_source_provenance(CDSCO_SOURCE_ID),
        )
        val_res = MedicineValidationResult(
            input_candidate="Amox...",
            normalized_candidate="amox",
            validation_status="uncertain",
            medicine_identity_status="uncertain",
            selected_reference=ref_cand,
            evidence="Token overlap match",
            requires_human_review=True,
            provenance=ValidationDecisionProvenance(
                retrieval_method="token_overlap",
                query_raw="Amox...",
                query_normalized="amox",
                normalization_version="v1.0",
                index_version="v1.0",
                config_hash="abc",
                matched_count=2,
                timestamp="2026-09-27T00:00:00Z",
                validation_rule="MULTI_CANDIDATE_AMBIGUITY_GATE",
                source_authorities=["cdsco"],
            )
        )
        identity_conf = extract_medicine_identity_confidence(name_field, val_res)
        assert identity_conf.conflict_detected is True
        assert identity_conf.visual_extraction_confidence.raw_value == 0.50
        assert identity_conf.reference_correspondence_confidence.raw_value == 0.98
        assert "Conflicting Evidence" in identity_conf.conflict_note

    def test_detect_confidence_conflicts_flags(self):
        med = ExtractedMedicine(
            medicine_name=ExtractedField(
                value="Amox...",
                status="uncertain",
                presence="present",
                extraction_state="ambiguous",
            ),
            dosage=ExtractedField(
                value="500 mg",
                status="confident",
                presence="present",
                extraction_state="extracted",
            ),
            frequency=ExtractedField(
                value="1-0-1",
                status="confident",
                presence="present",
                extraction_state="extracted",
            ),
            duration=ExtractedField(
                value="5 days",
                status="confident",
                presence="present",
                extraction_state="extracted",
            ),
        )
        val_res = MedicineValidationResult(
            input_candidate="Amox...",
            normalized_candidate="amox",
            validation_status="uncertain",
            medicine_identity_status="uncertain",
            evidence="Ambiguous candidates",
            requires_human_review=True,
            formulation_consistency="mismatch",
            provenance=ValidationDecisionProvenance(
                retrieval_method="token_overlap",
                query_raw="Amox...",
                query_normalized="amox",
                normalization_version="v1.0",
                index_version="v1.0",
                config_hash="abc",
                matched_count=2,
                timestamp="2026-09-27T00:00:00Z",
                validation_rule="MULTI_CANDIDATE_AMBIGUITY_GATE",
                source_authorities=["cdsco"],
            )
        )
        conflicts = detect_confidence_conflicts(med, val_res)
        assert "AMBIGUOUS_CURSIVE_STROKE" in conflicts
        assert "DOSAGE_FORMULATION_MISMATCH" in conflicts
        assert "MULTIPLE_REFERENCE_CANDIDATES" in conflicts

    def test_conflict_detection_exposes_metadata_without_human_review_decision(self):
        """
        Verifies that Phase 8 conflict detection strictly exposes conflict metadata
        without triggering, mandating, or executing human review or abstention routing.
        Human verification routing is strictly isolated to Phase 9.
        """
        ref_cand = RetrievalCandidate(
            reference_id="REF-CDSCO-002",
            source="cdsco-approved-drugs",
            medicine_name="Amoxicillin 500mg",
            match_method="token_overlap",
            score=0.98,
            strength="500 mg",
            evidence="Token overlap match",
            provenance=get_source_provenance(CDSCO_SOURCE_ID),
        )
        name_field = ExtractedField(
            value="Amox...",
            confidence=0.50,
            status="uncertain",
            presence="present",
            extraction_state="ambiguous",
            candidates=["Amoxicillin", "Ampicillin"],
        )
        dosage_field = ExtractedField(
            value="1000 mg",
            status="confident",
            presence="present",
            extraction_state="extracted",
        )
        val_res = MedicineValidationResult(
            input_candidate="Amox...",
            normalized_candidate="amox",
            validation_status="uncertain",
            medicine_identity_status="uncertain",
            selected_reference=ref_cand,
            evidence="Ambiguous candidates",
            requires_human_review=True,
            dosage_observation_preserved=True,
            observed_dosage="1000 mg",
            reference_strength="500 mg",
            formulation_consistency="mismatch",
            provenance=ValidationDecisionProvenance(
                retrieval_method="token_overlap",
                query_raw="Amox...",
                query_normalized="amox",
                normalization_version="v1.0",
                index_version="v1.0",
                config_hash="abc",
                matched_count=2,
                timestamp="2026-09-27T00:00:00Z",
                validation_rule="MULTI_CANDIDATE_AMBIGUITY_GATE",
                source_authorities=["cdsco"],
            )
        )
        identity_conf = extract_medicine_identity_confidence(name_field, val_res)
        dosage_conf = extract_dosage_confidence_signal(dosage_field, val_res)

        med = ExtractedMedicine(
            medicine_name=name_field,
            dosage=dosage_field,
            frequency=ExtractedField(value="1-0-1", status="confident", presence="present", extraction_state="extracted"),
            duration=ExtractedField(value="5 days", status="confident", presence="present", extraction_state="extracted"),
        )
        conflicts = detect_confidence_conflicts(med, val_res)

        # 1. Conflict metadata is exposed
        assert identity_conf.conflict_detected is True
        assert identity_conf.conflict_note is not None
        assert "Conflicting Evidence" in identity_conf.conflict_note
        assert "AMBIGUOUS_CURSIVE_STROKE" in conflicts
        assert "VISUAL_RETRIEVAL_DISCREPANCY" in conflicts
        assert "DOSAGE_FORMULATION_MISMATCH" in conflicts
        assert "MULTIPLE_REFERENCE_CANDIDATES" in conflicts

        # 2. Phase 8 schemas have NO human review execution fields or abstention decisions
        assert not hasattr(identity_conf, "execute_human_review")
        assert not hasattr(identity_conf, "mandates_clinician_review")
        assert not hasattr(identity_conf, "abstain")
        assert not hasattr(dosage_conf, "abstain")

        # 3. Dosage remains immutable (no dosage modification occurs)
        assert dosage_conf.observed_dosage == "1000 mg"
        assert dosage_conf.reference_strength == "500 mg"
        assert dosage_conf.reference_support_status == "mismatch"

