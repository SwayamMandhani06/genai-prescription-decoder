"""
Phase 10 Tests: LASA Similarity Engine.
Tests orthographic, phonetic, and combined similarity computations.
"""

import pytest
from ai.lasa.similarity import (
    orthographic_similarity,
    phonetic_similarity,
    metaphone_exact_match,
    combined_similarity,
    compute_metaphone,
    lookup_tall_man_pair,
)


class TestOrthographicSimilarity:
    """Tests for lexical/orthographic similarity using SequenceMatcher."""

    def test_identical_names(self):
        score = orthographic_similarity("Metformin", "Metformin")
        assert score == 1.0

    def test_identical_case_insensitive(self):
        score = orthographic_similarity("METFORMIN", "metformin")
        assert score == 1.0

    def test_similar_names_high(self):
        score = orthographic_similarity("Metformin", "Metronidazole")
        assert 0.3 < score < 0.9  # Similar prefix but different suffix

    def test_dissimilar_names(self):
        score = orthographic_similarity("Aspirin", "Omeprazole")
        assert score < 0.4

    def test_known_confusable_pair(self):
        score = orthographic_similarity("Prednisolone", "Prednisone")
        assert score > 0.7

    def test_empty_name(self):
        assert orthographic_similarity("", "Metformin") == 0.0
        assert orthographic_similarity("Metformin", "") == 0.0

    def test_chlorpromazine_chlorpropamide(self):
        score = orthographic_similarity("Chlorpromazine", "Chlorpropamide")
        assert score > 0.7

    def test_hydroxyzine_hydralazine(self):
        score = orthographic_similarity("Hydroxyzine", "Hydralazine")
        assert score > 0.6


class TestPhoneticSimilarity:
    """Tests for phonetic similarity via Double Metaphone."""

    def test_identical_names(self):
        score = phonetic_similarity("Metformin", "Metformin")
        assert score == 1.0

    def test_phonetically_similar(self):
        score = phonetic_similarity("Prednisolone", "Prednisone")
        assert score > 0.5

    def test_phonetically_different(self):
        score = phonetic_similarity("Aspirin", "Omeprazole")
        assert score < 0.6

    def test_empty_name(self):
        assert phonetic_similarity("", "Metformin") == 0.0


class TestMetaphoneExactMatch:
    """Tests for exact metaphone code matching."""

    def test_identical(self):
        assert metaphone_exact_match("Metformin", "Metformin") is True

    def test_different(self):
        assert metaphone_exact_match("Aspirin", "Metformin") is False

    def test_empty(self):
        assert metaphone_exact_match("", "Metformin") is False


class TestComputeMetaphone:
    """Tests for Double Metaphone code generation."""

    def test_nonempty_code(self):
        primary, secondary = compute_metaphone("Metformin")
        assert len(primary) > 0
        assert len(secondary) > 0

    def test_max_length(self):
        primary, _ = compute_metaphone("Chlorpromazine")
        assert len(primary) <= 6

    def test_empty(self):
        assert compute_metaphone("") == ("", "")

    def test_strips_numbers(self):
        primary, _ = compute_metaphone("Metformin 500mg")
        assert primary == compute_metaphone("Metformin")[0]


class TestCombinedSimilarity:
    """Tests for the combined weighted similarity function."""

    def test_returns_tuple_of_four(self):
        result = combined_similarity("Metformin", "Metronidazole")
        assert len(result) == 4

    def test_orthographic_and_phonetic_scores(self):
        ortho, phon, combo, meta = combined_similarity("Metformin", "Metronidazole")
        assert 0.0 <= ortho <= 1.0
        assert 0.0 <= phon <= 1.0
        assert 0.0 <= combo <= 1.0
        assert isinstance(meta, bool)

    def test_equal_weights(self):
        ortho, phon, combo, _ = combined_similarity(
            "Prednisolone", "Prednisone",
            ortho_weight=0.5,
            phonetic_weight=0.5,
        )
        expected = 0.5 * ortho + 0.5 * phon
        assert abs(combo - expected) < 0.001

    def test_custom_weights(self):
        ortho, phon, combo, _ = combined_similarity(
            "Prednisolone", "Prednisone",
            ortho_weight=0.8,
            phonetic_weight=0.2,
        )
        expected = 0.8 * ortho + 0.2 * phon
        assert abs(combo - expected) < 0.001


class TestLookupTallManPair:
    """Tests for known ISMP Tall Man pair lookup."""

    def test_known_pair_forward(self):
        result = lookup_tall_man_pair("Metformin", "Metronidazole")
        assert result is not None
        assert result[2] == "metFORMIN"
        assert result[3] == "metRONIDAZOLE"

    def test_known_pair_reverse(self):
        result = lookup_tall_man_pair("Metronidazole", "Metformin")
        assert result is not None
        assert result[2] == "metRONIDAZOLE"
        assert result[3] == "metFORMIN"

    def test_case_insensitive(self):
        result = lookup_tall_man_pair("METFORMIN", "METRONIDAZOLE")
        assert result is not None

    def test_unknown_pair(self):
        result = lookup_tall_man_pair("Aspirin", "Omeprazole")
        assert result is None

    def test_prednisolone_prednisone(self):
        result = lookup_tall_man_pair("Prednisolone", "Prednisone")
        assert result is not None
        assert "prednisoLONE" in (result[2], result[3])

    def test_vinblastine_vincristine(self):
        result = lookup_tall_man_pair("Vinblastine", "Vincristine")
        assert result is not None
