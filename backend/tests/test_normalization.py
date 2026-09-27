"""
Unit Tests for Deterministic Normalization and Clinical Safety Transformations (Phase 3)
"""

import pytest
from backend.app.dataset.normalization import (
    normalize_text,
    normalize_dosage,
    normalize_frequency,
    ClinicalNormalizer
)


def test_unicode_and_whitespace_normalization():
    """Verifies that non-standard spaces, Unicode ligatures, and tabs are collapsed cleanly."""
    raw = "Augmentin\t\u00a0625   mg  \n  (BD) "
    normalized = normalize_text(raw)
    assert normalized == "Augmentin 625 mg (BD)"


def test_dosage_unit_standardization():
    """Verifies standard medical dosage unit normalization."""
    cases = [
        ("625mg", 625.0, "mg", "625 mg"),
        ("500 mgs", 500.0, "mg", "500 mg"),
        ("100 mcg", 100.0, "mcg", "100 mcg"),
        ("50 ug", 50.0, "mcg", "50 mcg"),
        ("5 ml", 5.0, "ml", "5 ml"),
        ("1 tab", 1.0, "tab", "1 tab"),
        ("2 tabs", 2.0, "tab", "2 tab"),
        ("1 cap", 1.0, "cap", "1 cap"),
        ("200 IU", 200.0, "IU", "200 IU"),
    ]
    for raw, expected_num, expected_unit, expected_canon in cases:
        res = normalize_dosage(raw)
        assert res.numeric_value == expected_num, f"Failed on {raw}"
        assert res.unit == expected_unit, f"Failed unit on {raw}"
        assert res.canonical_string == expected_canon, f"Failed canon on {raw}"


def test_dosage_decimal_safety_preservation():
    """
    SAFETY TEST: Verifies that decimal numbers like 0.5 mg or 1.0 mg are NEVER mutated or misparsed.
    Must never convert 0.5 to 5 or 1.0 to 10.
    """
    res1 = normalize_dosage("0.5 mg")
    assert res1.numeric_value == 0.5
    assert res1.canonical_string == "0.5 mg"

    res2 = normalize_dosage("1.0 mg")
    assert res2.numeric_value == 1.0
    assert res2.canonical_string == "1.0 mg"
    assert res2.canonical_string != "10 mg"


def test_frequency_shorthand_normalization():
    """Verifies Latin abbreviations and Indian outpatient interval codes."""
    cases = [
        ("1-0-1", "BD", "Twice daily (Morning, Night)", 2),
        ("1-1-1", "TDS", "Three times daily (Morning, Afternoon, Night)", 3),
        ("1-0-0", "OD", "Once daily (Morning)", 1),
        ("0-0-1", "HS", "Once daily (At bedtime)", 1),
        ("BD", "BD", "Twice daily", 2),
        ("TID", "TDS", "Three times daily", 3),
        ("SOS", "SOS", "As needed / when necessary", 0),
        ("hs", "HS", "At bedtime", 1),
    ]
    for raw, exp_code, exp_exp, exp_count in cases:
        res = normalize_frequency(raw)
        assert res.is_valid is True, f"Failed validity on {raw}"
        assert res.canonical_code == exp_code, f"Failed code on {raw}"
        assert res.standard_expansion == exp_exp, f"Failed expansion on {raw}"
        assert res.daily_count == exp_count, f"Failed daily count on {raw}"


def test_clinical_normalizer_preserves_raw_tokens():
    """Verifies that batch normalization returns both normalized values and raw unmodified tokens."""
    res = ClinicalNormalizer.normalize_entity(
        medicine_name="Tab  Augmentin",
        dosage_strength="625mg",
        frequency="1 - 0 - 1"
    )
    assert res["original_name"] == "Tab  Augmentin"
    assert res["normalized_name"] == "Tab Augmentin"
    assert res["original_dosage"] == "625mg"
    assert res["dosage"]["canonical_string"] == "625 mg"
    assert res["original_frequency"] == "1 - 0 - 1"
    assert res["frequency"]["canonical_code"] == "BD"


def test_normalization_safety_raw_text_immutable_and_never_overwritten():
    """
    CRITICAL SAFETY TEST:
    Verifies that clinical normalization operations strictly preserve raw_text without overwriting.
    Normalized values must exist strictly as derived representations.
    """
    raw_doctor_ink = "Tab. Augmentin 625 Duo   (1 - 0 - 1)  5d  PC"
    
    # Perform normalization
    norm_result = ClinicalNormalizer.normalize_entity(
        medicine_name=raw_doctor_ink,
        dosage_strength="625 Duo",
        frequency="1 - 0 - 1"
    )

    # 1. Verify original input is strictly preserved and not overwritten
    assert norm_result["original_name"] == raw_doctor_ink
    assert norm_result["original_name"] != norm_result["normalized_name"]

    # 2. Check in medication entity annotation
    from backend.app.dataset.schema import MedicationEntityAnnotation, AmbiguityLevel
    med_entity = MedicationEntityAnnotation(
        item_index=1,
        raw_text=raw_doctor_ink,
        medicine_name=norm_result["normalized_name"],
        dosage_strength="625 mg",
        frequency="1-0-1",
        instructions="After food",
        ambiguity_level=AmbiguityLevel.NONE
    )

    # Explicit assertion: raw_text != overwritten by normalized name
    assert med_entity.raw_text == raw_doctor_ink
    assert med_entity.raw_text != med_entity.medicine_name
    assert med_entity.raw_text != "Augmentin"
    assert "Tab. Augmentin 625 Duo" in med_entity.raw_text
