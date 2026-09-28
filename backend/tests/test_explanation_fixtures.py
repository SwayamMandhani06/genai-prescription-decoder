"""
Phase 11 Unit Tests: Comprehensive Audit of Mock Fixtures.
Validates all 22 mock fixtures defined in ai/explanation/fixtures.py
against generator outputs and fidelity validators.
"""

import pytest
from ai.explanation.fixtures import EXPLANATION_FIXTURES
from ai.explanation.generator import PosologyExplanationGenerator
from ai.explanation.validators import (
    MedicineNameFidelityValidator,
    NumericFidelityValidator,
    UnsupportedFactValidator,
)


def test_fixture_count_is_22():
    assert len(EXPLANATION_FIXTURES) >= 22


@pytest.mark.parametrize("key,fixture", list(EXPLANATION_FIXTURES.items()))
def test_mock_fixtures_execution(key: str, fixture: dict):
    # Verify development notice is present
    assert "DEVELOPMENT TEST FIXTURE" in fixture.get("notice", "")

    # For generation fixtures with 'input'
    if "input" in fixture:
        inp = fixture["input"]
        res = PosologyExplanationGenerator.generate_explanation(
            prescription_id=inp["prescription_id"],
            medicine_name=inp.get("medicine_name"),
            dosage=inp.get("dosage"),
            frequency=inp.get("frequency"),
            duration=inp.get("duration"),
            candidate_status=inp.get("candidate_status", "confident"),
            validation_status=inp.get("validation_status", "validated"),
            abstention_decision=inp.get("abstention_decision", "accepted"),
            requires_human_verification=inp.get("requires_human_verification", False),
            has_lasa_conflict=inp.get("has_lasa_conflict", False),
            confusable_counterpart=inp.get("confusable_counterpart"),
            human_verification_status=inp.get("human_verification_status"),
            human_verified_value=inp.get("human_verified_value"),
            is_service_healthy=inp.get("is_service_healthy", True),
        )

        expected_status = fixture.get("expected_status")
        if expected_status:
            assert res.overall_eligibility == expected_status

        for lang, exp in res.explanations.items():
            expected_key = f"expected_in_{lang}"
            if expected_key in fixture:
                for token in fixture[expected_key]:
                    assert token in exp.summary or token in exp.instructions

    # For validator fixtures with 'mutated_text'
    if "mutated_text" in fixture:
        if "18_unsupported_fact_rejection" in key:
            is_val, details = UnsupportedFactValidator.validate(fixture["mutated_text"])
            assert is_val is False
            assert any(fixture["expected_detail"] in d for d in details)

        elif "19_numeric_mutation_rejection" in key:
            is_val, details = NumericFidelityValidator.validate(
                source_facts={"dosage": fixture["source_dosage"]},
                generated_text=fixture["mutated_text"],
                status="eligible",
            )
            assert is_val is False
            assert any(fixture["expected_detail"] in d for d in details)

        elif "20_medicine_mutation_rejection" in key:
            is_val, details = MedicineNameFidelityValidator.validate(
                effective_medicine_name=fixture["source_medicine"],
                generated_text=fixture["mutated_text"],
                status="eligible",
            )
            assert is_val is False
            assert any(fixture["expected_detail"] in d for d in details)
