"""
Phase 11 Unit Tests: Explanation Schemas and Configuration.
Tests schema validation, immutable config hashing, provenance metadata,
and data models.
"""

import pytest
from ai.explanation.config import (
    CONFIG_HASH,
    DEFAULT_EXPLANATION_CONFIG,
    EXPLANATION_PROVENANCE_METADATA,
    POLICY_VERSION,
    SUPPORTED_LANGUAGES,
    TEMPLATE_VERSION,
    TERMINOLOGY_VERSION,
    ExplanationConfig,
)
from ai.explanation.schemas import (
    ExplanationEligibilityStatus,
    ExplanationResult,
    ExplanationValidationResult,
    LanguageExplanationPack,
    MultilingualPrescriptionExplanation,
    PosologyTimingSlot,
)


def test_explanation_config_defaults():
    config = ExplanationConfig()
    assert config.policy_version == "explanation_policy_v1"
    assert config.template_version == "explanation_template_v1"
    assert config.terminology_version == "explanation_terminology_v1"
    assert config.supported_languages == ["en", "hi", "mr"]
    assert config.enforce_numeric_fidelity is True
    assert config.enforce_medicine_fidelity is True
    assert config.enforce_unsupported_fact_check is True
    assert config.allow_unverified_definitive_instruction is False


def test_config_hash_deterministic():
    c1 = ExplanationConfig()
    c2 = ExplanationConfig()
    assert c1.config_hash == c2.config_hash
    assert len(c1.config_hash) == 64
    assert c1.config_hash == CONFIG_HASH


def test_config_hash_mutates_on_policy_change():
    c1 = ExplanationConfig()
    c2 = ExplanationConfig(enforce_numeric_fidelity=False)
    assert c1.config_hash != c2.config_hash


def test_posology_timing_slot_validation():
    slot = PosologyTimingSlot(
        time_slot="Morning",
        icon_key="sun",
        dosage_label="500 mg",
        food_instruction="After meals",
    )
    assert slot.time_slot == "Morning"
    assert slot.icon_key == "sun"
    assert slot.dosage_label == "500 mg"
    assert slot.food_instruction == "After meals"


def test_explanation_validation_result_is_valid():
    v_pass = ExplanationValidationResult(
        medicine_fidelity=True,
        numeric_fidelity=True,
        unsupported_fact_check=True,
    )
    assert v_pass.is_valid is True

    v_fail = ExplanationValidationResult(
        medicine_fidelity=True,
        numeric_fidelity=False,
        unsupported_fact_check=True,
        details=["Number mutated"],
    )
    assert v_fail.is_valid is False


def test_multilingual_explanation_consistency_validator():
    val = ExplanationValidationResult(
        medicine_fidelity=True,
        numeric_fidelity=True,
        unsupported_fact_check=True,
    )
    exp_en = ExplanationResult(
        status="eligible",
        language="en",
        summary="Paracetamol is listed with a dose of 500 mg.",
        instructions="Take Paracetamol 500 mg.",
        validation=val,
    )
    exp_hi = ExplanationResult(
        status="eligible",
        language="hi",
        summary="प्रिस्क्रिप्शन में Paracetamol की मात्रा 500 mg लिखी है।",
        instructions="Paracetamol लें।",
        validation=val,
    )
    exp_mr = ExplanationResult(
        status="eligible",
        language="mr",
        summary="प्रिस्क्रिप्शनमध्ये Paracetamol ची मात्रा 500 mg लिहिलेली आहे.",
        instructions="Paracetamol घ्या.",
        validation=val,
    )

    full = MultilingualPrescriptionExplanation(
        prescription_id="RX-001",
        overall_eligibility="eligible",
        explanations={"en": exp_en, "hi": exp_hi, "mr": exp_mr},
        policy_version=POLICY_VERSION,
        template_version=TEMPLATE_VERSION,
        config_hash=CONFIG_HASH,
    )
    assert full.prescription_id == "RX-001"
    assert full.overall_eligibility == "eligible"
    assert "en" in full.explanations
    assert "hi" in full.explanations
    assert "mr" in full.explanations


def test_provenance_metadata_contains_invariants():
    assert "factual_invariants" in EXPLANATION_PROVENANCE_METADATA
    assert len(EXPLANATION_PROVENANCE_METADATA["factual_invariants"]) >= 4
    assert "scope_disclosure" in EXPLANATION_PROVENANCE_METADATA
