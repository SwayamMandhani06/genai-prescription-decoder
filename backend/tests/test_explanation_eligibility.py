"""
Phase 11 Unit Tests: Explanation Eligibility Gate.
Tests eligibility transitions across all clinical dimensions:
1. Confident + Validated -> Eligible
2. Uncertain medicine name -> Restricted
3. LASA conflict -> Restricted
4. Phase 9 Abstention -> Abstained
5. Human verified correction -> Eligible with corrected entity
6. Human marked unreadable -> Abstained
7. Missing medicine name -> Abstained
8. Service unhealthy -> Unavailable
"""

import pytest
from ai.explanation.eligibility import ExplanationEligibilityGate, EligibilityEvaluation


def test_confident_validated_is_eligible():
    eval_res = ExplanationEligibilityGate.evaluate(
        candidate_name="Paracetamol",
        candidate_status="confident",
        validation_status="validated",
        abstention_decision="accepted",
        requires_human_verification=False,
        has_lasa_conflict=False,
    )
    assert eval_res.status == "eligible"
    assert eval_res.effective_medicine_name == "Paracetamol"
    assert eval_res.reason == "CONFIDENT_VALIDATED_ELIGIBLE"


def test_uncertain_extraction_is_restricted():
    eval_res = ExplanationEligibilityGate.evaluate(
        candidate_name="Amoxi...",
        candidate_status="uncertain",
        validation_status="uncertain",
        abstention_decision="accepted",
        requires_human_verification=True,
        has_lasa_conflict=False,
    )
    assert eval_res.status == "restricted"
    assert eval_res.effective_medicine_name == "Amoxi..."
    assert eval_res.reason == "EXTRACTION_OR_VALIDATION_UNCERTAIN"


def test_lasa_conflict_is_restricted():
    eval_res = ExplanationEligibilityGate.evaluate(
        candidate_name="Prednisone",
        candidate_status="confident",
        validation_status="validated",
        abstention_decision="accepted",
        requires_human_verification=True,
        has_lasa_conflict=True,
        confusable_counterpart="Prednisolone",
    )
    assert eval_res.status == "restricted"
    assert eval_res.has_lasa_conflict is True
    assert eval_res.confusable_name == "Prednisolone"
    assert eval_res.reason == "LASA_SIMILARITY_CONFLICT"


def test_phase9_abstention_is_abstained():
    eval_res = ExplanationEligibilityGate.evaluate(
        candidate_name="UncertainMed",
        candidate_status="abstained",
        validation_status="not_validated",
        abstention_decision="abstained",
        requires_human_verification=True,
        has_lasa_conflict=False,
    )
    assert eval_res.status == "abstained"
    assert eval_res.reason == "PHASE9_CLINICAL_ABSTENTION"


def test_human_correction_is_eligible_with_corrected_entity():
    eval_res = ExplanationEligibilityGate.evaluate(
        candidate_name="Amox...",
        candidate_status="uncertain",
        validation_status="validated",
        abstention_decision="accepted",
        requires_human_verification=False,
        has_lasa_conflict=False,
        human_verification_status="corrected",
        human_verified_value="Amoxicillin",
    )
    assert eval_res.status == "eligible"
    assert eval_res.effective_medicine_name == "Amoxicillin"
    assert eval_res.original_ai_name == "Amox..."
    assert eval_res.is_human_corrected is True
    assert eval_res.reason == "HUMAN_VERIFIED_CORRECTION"


def test_human_confirmed_is_eligible():
    eval_res = ExplanationEligibilityGate.evaluate(
        candidate_name="Metformin",
        candidate_status="confident",
        validation_status="validated",
        abstention_decision="accepted",
        requires_human_verification=False,
        has_lasa_conflict=False,
        human_verification_status="confirmed",
    )
    assert eval_res.status == "eligible"
    assert eval_res.effective_medicine_name == "Metformin"
    assert eval_res.is_human_confirmed is True


def test_human_marked_unreadable_is_abstained():
    eval_res = ExplanationEligibilityGate.evaluate(
        candidate_name="Scribble",
        candidate_status="abstained",
        validation_status="unverified",
        abstention_decision="abstained",
        requires_human_verification=True,
        has_lasa_conflict=False,
        human_verification_status="unreadable",
    )
    assert eval_res.status == "abstained"
    assert eval_res.is_unreadable is True
    assert eval_res.reason == "HUMAN_MARKED_UNREADABLE"


def test_missing_medicine_name_is_abstained():
    for empty_val in [None, "", "   ", "Not Observed", "unknown medicine"]:
        eval_res = ExplanationEligibilityGate.evaluate(
            candidate_name=empty_val,
            candidate_status="confident",
            validation_status="validated",
        )
        assert eval_res.status == "abstained"
        assert eval_res.reason == "MEDICINE_NAME_MISSING"


def test_unhealthy_service_is_unavailable():
    eval_res = ExplanationEligibilityGate.evaluate(
        candidate_name="Paracetamol",
        is_service_healthy=False,
    )
    assert eval_res.status == "unavailable"
    assert eval_res.reason == "EXPLANATION_SERVICE_UNAVAILABLE"
