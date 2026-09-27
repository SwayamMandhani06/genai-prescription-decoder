"""
Unit tests for Phase 7 Evidence-Grounded Medicine Validation Decision Engine.
Adheres to Sections 1, 2, 11, 12, 13, and 14 of PLAN.md:
- Preserves uncertainty when evidence is ambiguous
- NEVER mutates prescription candidates or dosage observations
- Preserves brand / generic separation
- Full audit provenance
"""

import pytest
from pathlib import Path
from ai.rag.service import get_medicine_validation_service
from ai.rag.schemas import MedicineValidationResult


@pytest.fixture(scope="module")
def validation_service():
    return get_medicine_validation_service()


class TestRAGValidator:
    def test_exact_match_autonomous_validation(self, validation_service):
        res = validation_service.validate_candidate("Augmentin 625 Duo")
        assert isinstance(res, MedicineValidationResult)
        assert res.validation_status == "validated"
        assert res.requires_human_review is False
        assert res.selected_reference is not None
        assert res.selected_reference.medicine_name == "Augmentin 625 Duo"
        assert "Augmentin 625 Duo" in res.evidence
        assert res.provenance.validation_rule == "HIGH_CONFIDENCE_FORMULARY_VALIDATED"

    def test_alias_match_autonomous_validation(self, validation_service):
        res = validation_service.validate_candidate("Clavam 625")
        assert res.validation_status == "validated"
        assert res.requires_human_review is False
        assert res.selected_reference is not None
        assert res.selected_reference.medicine_name == "Augmentin 625 Duo"

    def test_multiple_candidates_ambiguity_preserves_uncertainty(self, validation_service):
        # "Amoxicillin" matches both CDSCO Amoxicillin 500mg and RxNorm Amoxicillin 500 MG Capsule
        res = validation_service.validate_candidate("Amoxicillin")
        assert res.validation_status == "uncertain"
        assert res.requires_human_review is True
        # Must NOT arbitrarily choose one!
        assert res.selected_reference is None
        assert len(res.matched_candidates) >= 2
        assert "Multiple plausible" in res.evidence or "uncertain" in res.evidence.lower()
        assert res.provenance.validation_rule == "MULTI_CANDIDATE_AMBIGUITY_GATE"

    def test_truncated_cursive_candidate_preserves_uncertainty(self, validation_service):
        res = validation_service.validate_candidate("Amox...")
        assert res.validation_status == "uncertain"
        assert res.requires_human_review is True
        assert res.selected_reference is None

    def test_unsupported_candidate_not_validated(self, validation_service):
        res = validation_service.validate_candidate("NonExistentMedicament999")
        assert res.validation_status == "not_validated"
        assert res.requires_human_review is True
        assert res.selected_reference is None
        assert len(res.matched_candidates) == 0
        assert "no corresponding approved formulation" in res.evidence

    def test_empty_candidate_rejection(self, validation_service):
        res = validation_service.validate_candidate("   ")
        assert res.validation_status == "not_validated"
        assert res.requires_human_review is True
        assert res.selected_reference is None
        assert "No medicine name candidate was extracted" in res.evidence

    def test_dosage_preservation_invariant_without_mutation(self, validation_service):
        # Observed dosage differs from standard reference strength (1000 mg vs 625 mg)
        res = validation_service.validate_candidate("Augmentin 625 Duo", observed_dosage="1000 mg")
        # Medicine identity is validated based on nomenclature match
        assert res.validation_status == "validated"
        assert res.medicine_identity_status == "validated"
        # Dosage observation MUST be preserved verbatim and never mutated
        assert res.dosage_observation_preserved is True
        assert res.observed_dosage == "1000 mg"
        # Reference strength remains independent
        assert res.reference_strength == "625 mg"
        assert res.selected_reference.strength == "625 mg"
        # Formulation consistency must be flagged as mismatch, not silently passed
        assert res.formulation_consistency == "mismatch"
        # Human review must be required when there is a formulation/dosage mismatch
        assert res.requires_human_review is True
        # Input candidate text must remain unchanged
        assert res.input_candidate == "Augmentin 625 Duo"

    def test_formulation_consistency_matching(self, validation_service):
        # Matching dosage
        res = validation_service.validate_candidate("Augmentin 625 Duo", observed_dosage="625 mg")
        assert res.validation_status == "validated"
        assert res.medicine_identity_status == "validated"
        assert res.dosage_observation_preserved is True
        assert res.observed_dosage == "625 mg"
        assert res.reference_strength == "625 mg"
        assert res.formulation_consistency == "consistent"
        assert res.requires_human_review is False

    def test_authoritative_sources_scope_and_licensing_metadata(self):
        from ai.rag.sources import AUTHORITATIVE_SOURCES, SOURCE_JUSTIFICATIONS, CDSCO_SOURCE_ID, RXNORM_SOURCE_ID
        # CDSCO scope checks
        cdsco = AUTHORITATIVE_SOURCES[CDSCO_SOURCE_ID]
        assert "finite development subset" in cdsco.source_version
        assert "Open Government Data License" in cdsco.license
        cdsco_just = SOURCE_JUSTIFICATIONS[CDSCO_SOURCE_ID]
        assert "finite CDSCO-derived reference subset" in cdsco_just
        assert "not a comprehensive representation" in cdsco_just

        # RxNorm scope & licensing checks
        rxnorm = AUTHORITATIVE_SOURCES[RXNORM_SOURCE_ID]
        assert "frozen reference fixture subset" in rxnorm.source_version
        assert "UMLS" in rxnorm.license
        assert "UTS access required" in rxnorm.license
        rxnorm_just = SOURCE_JUSTIFICATIONS[RXNORM_SOURCE_ID]
        assert "U.S.-centric and should not be treated as a comprehensive Indian formulary" in rxnorm_just
        assert "Current NLM releases are newer" in rxnorm_just
        assert "clinical validation" not in rxnorm.license.lower() or "free for clinical validation" not in rxnorm.license.lower()

    def test_dosage_mismatch_in_ui_evidence(self, validation_service):
        res = validation_service.validate_candidate("Augmentin 625 Duo", observed_dosage="1000 mg")
        ui_evidence = res.to_ui_validation_evidence()
        assert ui_evidence["formulation_consistency"] == "mismatch"
        assert ui_evidence["observed_dosage"] == "1000 mg"
        assert ui_evidence["reference_strength"] == "625 mg"
        assert "DOSAGE MISMATCH" in ui_evidence["status_badge_text"]
        assert ui_evidence["dosage_mismatch_warning"] is not None

    def test_brand_generic_relationship_retention(self, validation_service):
        res = validation_service.validate_candidate("Augmentin")
        assert res.brand_generic_relationship is not None
        assert res.brand_generic_relationship.get("brand_name") == "Augmentin"
        assert "Amoxicillin" in res.brand_generic_relationship.get("generic_name")

    def test_to_ui_validation_evidence_structure(self, validation_service):
        res = validation_service.validate_candidate("Augmentin 625 Duo")
        ui_evidence = res.to_ui_validation_evidence()
        assert ui_evidence["candidate_name"] == "Augmentin 625 Duo"
        assert ui_evidence["matched_entity_name"] == "Augmentin 625 Duo"
        assert ui_evidence["validation_status"] in ("cdsco_approved", "rxnorm_grounded")
        assert ui_evidence["cdsco_schedule"] is not None
        assert ui_evidence["rxnorm_cui"] is not None
        assert ui_evidence["therapeutic_class"] is not None
        assert ui_evidence["evidence_source"] is not None
