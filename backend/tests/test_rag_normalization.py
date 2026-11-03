"""
Unit tests for Phase 7 conservative medicine name normalization.
Adheres to Section 8 of PLAN.md:
- Unicode NFKC normalization
- Whitespace stripping and collapsing
- Deterministic safe punctuation handling
- Raw vs normalized candidate separation (never mutates raw string)
"""

import pytest
from ai.rag.normalization import (
    NORMALIZATION_VERSION,
    normalize_medicine_name,
    extract_tokens,
    token_set,
    separate_raw_and_normalized,
)


class TestRAGNormalization:
    def test_version_identifier(self):
        assert NORMALIZATION_VERSION in ("v1.0-conservative", "v1.1-indian-posology")

    def test_empty_and_whitespace_input(self):
        assert normalize_medicine_name("") == ""
        assert normalize_medicine_name("   ") == ""
        assert normalize_medicine_name(None) == ""

    def test_unicode_nfkc_normalization(self):
        # Fullwidth Latin characters should normalize to standard ASCII
        fullwidth_str = "Ａｕｇｍｅｎｔｉｎ"
        norm = normalize_medicine_name(fullwidth_str)
        assert norm == "augmentin"

    def test_case_folding(self):
        assert normalize_medicine_name("AUGMENTIN 625 DUO") == "augmentin 625 duo"
        assert normalize_medicine_name("AmOxiCiLlin") == "amoxicillin"

    def test_safe_punctuation_handling(self):
        # Hyphens, slashes, plus signs, brackets should be replaced by spaces
        raw = "Amox/Clav (500+125mg)-Tab."
        norm = normalize_medicine_name(raw)
        assert norm == "amox clav 500 125mg tab"

    def test_whitespace_collapsing(self):
        raw = "   Augmentin    \t\n  625   Duo   "
        norm = normalize_medicine_name(raw)
        assert norm == "augmentin 625 duo"

    def test_extract_tokens(self):
        tokens = extract_tokens("Augmentin 625 Duo (Amoxicillin + Clav)")
        assert tokens == ["augmentin", "625", "duo", "amoxicillin", "clav"]

    def test_token_set(self):
        s = token_set("Amoxicillin 500mg Amoxicillin")
        assert s == {"amoxicillin", "500mg"}

    def test_separate_raw_and_normalized_invariant(self):
        raw_input = "  Amox/Clav 625mg  "
        raw, norm = separate_raw_and_normalized(raw_input)
        # Raw must remain completely identical
        assert raw == "  Amox/Clav 625mg  "
        # They must be separate objects
        assert raw != norm

    def test_indian_frequency_normalization(self):
        from ai.rag.normalization import normalize_indian_frequency

        raw, norm = normalize_indian_frequency("1-0-1")
        assert raw == "1-0-1"
        assert norm == "BD (Twice daily - Morning, Night)"

        _, norm_tds = normalize_indian_frequency("1-1-1")
        assert norm_tds == "TDS (Three times daily)"

        _, norm_od = normalize_indian_frequency("1-0-0")
        assert norm_od == "OD (Once daily - Morning)"

        _, norm_night = normalize_indian_frequency("0-0-1")
        assert norm_night == "Once daily at bedtime"

        _, norm_prn = normalize_indian_frequency("SOS")
        assert norm_prn == "As needed"

        _, norm_hs = normalize_indian_frequency("hs")
        assert norm_hs == "Once daily at bedtime"

        raw_pc, norm_pc = normalize_indian_frequency("1-0-1 pc")
        assert raw_pc == "1-0-1 pc"
        assert norm_pc == "BD (Twice daily - Morning, Night)"

    def test_indian_duration_normalization(self):
        from ai.rag.normalization import normalize_indian_duration

        raw5, norm5 = normalize_indian_duration("5/7")
        assert raw5 == "5/7"
        assert norm5 == "5 days"

        _, norm_w = normalize_indian_duration("2/52")
        assert norm_w == "2 weeks"

        _, norm_m = normalize_indian_duration("1/12")
        assert norm_m == "1 month"

        raw10, norm10 = normalize_indian_duration("10 days")
        assert raw10 == "10 days"
        assert norm10 == "10 days"

    def test_corroborate_numeric_brand_suffix(self):
        from ai.rag.normalization import corroborate_numeric_brand_suffix

        # Augmentin 625 is in CDSCO reference data (Amoxicillin 500mg + Clavulanic Acid 125mg = 625mg)
        base, strength = corroborate_numeric_brand_suffix("Augmentin 625")
        assert "Augmentin" in base
        assert strength is not None
        assert "625" in strength

        # Unknown drug with number: do NOT fabricate units or strength!
        base_unk, strength_unk = corroborate_numeric_brand_suffix("UnknownDrug 999")
        assert strength_unk is None

