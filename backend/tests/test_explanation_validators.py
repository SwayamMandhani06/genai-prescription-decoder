"""
Phase 11 Unit Tests: Explanation Safety and Fidelity Validators.
Tests:
1. NumericFidelityValidator (decimals, numbers, units, mutations)
2. MedicineNameFidelityValidator (Roman script preservation, mutations)
3. UnsupportedFactValidator (rejection of ungrounded indications, diagnoses, prognosis, dosage changes)
"""

import pytest
from ai.explanation.validators import (
    ExplanationFidelityValidator,
    MedicineNameFidelityValidator,
    NumericFidelityValidator,
    UnsupportedFactValidator,
)


def test_numeric_fidelity_passes_verbatim_values():
    source_facts = {"dosage": "500 mg", "duration": "5 days"}
    generated_text = "Paracetamol is listed with a dose of 500 mg, for 5 days."
    is_valid, details = NumericFidelityValidator.validate(
        source_facts=source_facts,
        generated_text=generated_text,
        status="eligible",
    )
    assert is_valid is True
    assert len(details) == 0


def test_numeric_fidelity_rejects_dosage_mutation():
    source_facts = {"dosage": "500 mg", "duration": "5 days"}
    # Mutated 500 mg -> 250 mg
    generated_text = "Paracetamol is listed with a dose of 250 mg, for 5 days."
    is_valid, details = NumericFidelityValidator.validate(
        source_facts=source_facts,
        generated_text=generated_text,
        status="eligible",
    )
    assert is_valid is False
    assert any("500" in d for d in details)


def test_numeric_fidelity_rejects_duration_mutation():
    source_facts = {"dosage": "500 mg", "duration": "5 days"}
    # Mutated 5 days -> 7 days
    generated_text = "Paracetamol is listed with a dose of 500 mg, for 7 days."
    is_valid, details = NumericFidelityValidator.validate(
        source_facts=source_facts,
        generated_text=generated_text,
        status="eligible",
    )
    assert is_valid is False
    assert any("5" in d for d in details)


def test_numeric_fidelity_preserves_decimals():
    source_facts = {"dosage": "2.5 mL", "duration": "3 days"}
    # 2.5 mL preserved verbatim
    text_ok = "Take 2.5 mL for 3 days."
    is_valid, details = NumericFidelityValidator.validate(
        source_facts=source_facts,
        generated_text=text_ok,
        status="eligible",
    )
    assert is_valid is True

    # Decimal mutated: 2.5 mL -> 2 mL
    text_mutated = "Take 2 mL for 3 days."
    is_valid_mut, details_mut = NumericFidelityValidator.validate(
        source_facts=source_facts,
        generated_text=text_mutated,
        status="eligible",
    )
    assert is_valid_mut is False
    assert any("2.5" in d for d in details_mut)


def test_medicine_fidelity_passes_verbatim_name():
    is_valid, details = MedicineNameFidelityValidator.validate(
        effective_medicine_name="Paracetamol",
        generated_text="Paracetamol is listed with 500 mg.",
        status="eligible",
    )
    assert is_valid is True


def test_medicine_fidelity_rejects_altered_name():
    is_valid, details = MedicineNameFidelityValidator.validate(
        effective_medicine_name="Paracetamol",
        generated_text="Ibuprofen is listed with 500 mg.",
        status="eligible",
    )
    assert is_valid is False
    assert any("Paracetamol" in d for d in details)


def test_unsupported_fact_validator_rejects_diagnoses_and_indications():
    forbidden_samples = [
        "Paracetamol is listed with a dose of 500 mg for fever.",
        "Take Amoxicillin 500 mg for infection.",
        "Take Ibuprofen 400 mg to treat pain.",
        "प्रिस्क्रिप्शन में दवा बुखार के लिए लिखी है।",
        "ताप असल्यास औषध घ्या.",
    ]
    for text in forbidden_samples:
        is_valid, details = UnsupportedFactValidator.validate(generated_text=text)
        assert is_valid is False, f"Expected rejection for: '{text}'"
        assert len(details) > 0


def test_unsupported_fact_validator_rejects_dosage_alterations():
    forbidden_samples = [
        "You can increase the dose if symptoms persist.",
        "खुराक बढ़ाएं यदि दर्द हो।",
        "डोस वाढवा.",
    ]
    for text in forbidden_samples:
        is_valid, details = UnsupportedFactValidator.validate(generated_text=text)
        assert is_valid is False
        assert any("claim detected" in d for d in details)


def test_unsupported_fact_validator_passes_approved_posology():
    clean_text = "Paracetamol is listed with a dose of 500 mg, to be taken twice daily, as written on the prescription."
    is_valid, details = UnsupportedFactValidator.validate(generated_text=clean_text)
    assert is_valid is True
    assert len(details) == 0


def test_composite_fidelity_validator():
    rep = ExplanationFidelityValidator.validate_explanation(
        language="en",
        status="eligible",
        effective_medicine_name="Paracetamol",
        source_facts={"dosage": "500 mg", "duration": "5 days"},
        generated_text="Paracetamol is listed with a dose of 500 mg, to be taken twice daily for 5 days, as written on the prescription.",
    )
    assert rep.is_valid is True
    assert rep.medicine_fidelity is True
    assert rep.numeric_fidelity is True
    assert rep.unsupported_fact_check is True
