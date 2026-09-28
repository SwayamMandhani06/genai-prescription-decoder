"""
Phase 11 Unit Tests: Cross-Language Consistency and Numeric Preservation.
Tests:
1. Section 33: Cross-Language Consistency across EN, HI, MR.
2. Section 34: Numeric Cross-Language Invariants (500 mg, twice daily, 5 days, decimals).
"""

import pytest
from ai.explanation.generator import PosologyExplanationGenerator
from ai.explanation.schemas import MultilingualPrescriptionExplanation


def test_cross_language_consistency_eligible_prescription():
    """
    Section 33: For identical structured facts, EN, HI, MR must preserve
    same medicine name, numeric dosage, frequency equivalent, and duration.
    """
    res: MultilingualPrescriptionExplanation = PosologyExplanationGenerator.generate_explanation(
        prescription_id="RX-CROSS-001",
        medicine_name="Paracetamol",
        dosage="500 mg",
        frequency="twice daily",
        duration="5 days",
        candidate_status="confident",
        validation_status="validated",
        abstention_decision="accepted",
        requires_human_verification=False,
        has_lasa_conflict=False,
    )

    assert res.overall_eligibility == "eligible"
    assert "en" in res.explanations
    assert "hi" in res.explanations
    assert "mr" in res.explanations

    en = res.explanations["en"]
    hi = res.explanations["hi"]
    mr = res.explanations["mr"]

    # Invariant 1: Medicine identity is verbatim across all 3 vernaculars
    assert "Paracetamol" in en.summary
    assert "Paracetamol" in hi.summary
    assert "Paracetamol" in mr.summary

    # Invariant 2: Numeric dosage is verbatim across all 3 vernaculars
    assert "500 mg" in en.summary
    assert "500 mg" in hi.summary
    assert "500 mg" in mr.summary

    # Invariant 3: Duration number 5 is preserved
    assert "5" in en.summary
    assert "5" in hi.summary
    assert "5" in mr.summary

    # Invariant 4: Frequency concept equivalence
    assert "twice daily" in en.summary
    assert "दो बार" in hi.summary
    assert "दोन वेळा" in mr.summary

    # Invariant 5: Eligibility state is identical
    assert en.status == hi.status == mr.status == "eligible"

    # Invariant 6: All three pass fidelity validation
    assert en.validation.is_valid is True
    assert hi.validation.is_valid is True
    assert mr.validation.is_valid is True


def test_cross_language_numeric_invariants_with_decimals():
    """
    Section 34: Exact decimal and multi-digit values (2.5 mL, 1000 mg)
    must remain unmutated across EN, HI, MR.
    """
    res = PosologyExplanationGenerator.generate_explanation(
        prescription_id="RX-DEC-002",
        medicine_name="Cough Syrup",
        dosage="2.5 mL",
        frequency="three times daily",
        duration="7 days",
    )

    for lang in ("en", "hi", "mr"):
        exp = res.explanations[lang]
        assert "2.5" in exp.summary
        assert "7" in exp.summary
        assert exp.validation.numeric_fidelity is True


def test_cross_language_consistency_uncertain_state():
    """
    When field is uncertain, all 3 languages must preserve conservative
    uncertainty without fabricating medicine names.
    """
    res = PosologyExplanationGenerator.generate_explanation(
        prescription_id="RX-UNC-003",
        medicine_name="Amoxi...",
        candidate_status="uncertain",
        requires_human_verification=True,
    )

    assert res.overall_eligibility == "restricted"
    en = res.explanations["en"]
    hi = res.explanations["hi"]
    mr = res.explanations["mr"]

    assert en.status == hi.status == mr.status == "restricted"
    assert "could not be read with sufficient confidence" in en.summary
    assert "पर्याप्त विश्वास के साथ पढ़ा नहीं जा सका" in hi.summary
    assert "पुरेशा खात्रीने वाचता आले नाही" in mr.summary


def test_cross_language_consistency_lasa_state():
    """
    When LASA conflict is detected, all 3 languages must instruct verification
    and neither assumes one candidate is correct.
    """
    res = PosologyExplanationGenerator.generate_explanation(
        prescription_id="RX-LASA-004",
        medicine_name="Prednisone",
        has_lasa_conflict=True,
        confusable_counterpart="Prednisolone",
    )

    assert res.overall_eligibility == "restricted"
    en = res.explanations["en"]
    hi = res.explanations["hi"]
    mr = res.explanations["mr"]

    assert en.status == hi.status == mr.status == "restricted"
    assert "Similar medicine names were detected" in en.summary
    assert "मिलते-जुलते दवा के नाम पाए गए हैं" in hi.summary
    assert "सारखी औषधांची नावे आढळली आहेत" in mr.summary
