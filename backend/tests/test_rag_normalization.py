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
        assert NORMALIZATION_VERSION == "v1.0-conservative"

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
        assert norm == "amox clav 625mg"
        # They must be separate objects
        assert raw != norm
