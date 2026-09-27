"""
Phase 5 Test Suite: OCR/HTR Evaluation Metrics
Validates Levenshtein DP edit distance, CER, WER, normalization rules,
and clinical entity Precision/Recall/F1 using deterministic synthetic test vectors.
"""

import pytest
from backend.app.ocr.metrics import (
    compute_cer,
    compute_wer,
    compute_entity_metrics,
    evaluate_ocr_hypothesis,
    levenshtein_distance_dp,
    normalize_eval_text,
)


class TestLevenshteinDistanceDP:
    """Verifies low-level dynamic programming Levenshtein algorithm and backtracked edits."""

    def test_identical_sequences(self):
        dist, subs, dels, ins = levenshtein_distance_dp("amoxicillin", "amoxicillin")
        assert dist == 0
        assert subs == 0
        assert dels == 0
        assert ins == 0

    def test_single_substitution(self):
        # 'a' -> 'o'
        dist, subs, dels, ins = levenshtein_distance_dp("cat", "cot")
        assert dist == 1
        assert subs == 1
        assert dels == 0
        assert ins == 0

    def test_single_deletion(self):
        # 's' deleted
        dist, subs, dels, ins = levenshtein_distance_dp("cats", "cat")
        assert dist == 1
        assert subs == 0
        assert dels == 1
        assert ins == 0

    def test_single_insertion(self):
        # 's' inserted
        dist, subs, dels, ins = levenshtein_distance_dp("cat", "cats")
        assert dist == 1
        assert subs == 0
        assert dels == 0
        assert ins == 1

    def test_empty_reference(self):
        dist, subs, dels, ins = levenshtein_distance_dp("", "hello")
        assert dist == 5
        assert ins == 5
        assert dels == 0
        assert subs == 0

    def test_empty_hypothesis(self):
        dist, subs, dels, ins = levenshtein_distance_dp("hello", "")
        assert dist == 5
        assert dels == 5
        assert ins == 0
        assert subs == 0

    def test_known_compound_distance(self):
        # "kitten" -> "sitting": k->s (sub), e->i (sub), +g (ins) = 3 edits
        dist, subs, dels, ins = levenshtein_distance_dp("kitten", "sitting")
        assert dist == 3
        assert dist == (subs + dels + ins)


class TestCERCalculation:
    """Verifies Character Error Rate (CER) computation on known synthetic strings."""

    def test_exact_match_cer(self):
        cer, breakdown = compute_cer("Paracetamol 500 mg", "Paracetamol 500 mg")
        assert cer == 0.0
        assert breakdown.total_edits == 0
        assert breakdown.reference_length == len("paracetamol 500 mg")

    def test_both_empty_cer(self):
        cer, breakdown = compute_cer("", "")
        assert cer == 0.0
        assert breakdown.total_edits == 0
        assert breakdown.reference_length == 0

    def test_empty_reference_nonempty_hypothesis_cer(self):
        cer, breakdown = compute_cer("", "Amoxicillin")
        assert cer == 1.0
        assert breakdown.insertions == len("amoxicillin")

    def test_known_cer_ratio(self):
        # Ref: "abcde" (5 chars), Hyp: "abxde" (1 sub) -> CER = 1/5 = 0.20
        cer, breakdown = compute_cer("abcde", "abxde", normalize=False)
        assert pytest.approx(cer, 0.001) == 0.20
        assert breakdown.substitutions == 1
        assert breakdown.reference_length == 5

    def test_high_cer_transcription_error(self):
        # Handwriting often introduces high CER (e.g. substitutions and deletions)
        cer, breakdown = compute_cer("Augmentin 625mg", "actrees 25mg")
        assert cer > 0.4
        assert breakdown.reference_length > 0


class TestWERCalculation:
    """Verifies Word Error Rate (WER) computation on known synthetic strings."""

    def test_exact_match_wer(self):
        wer, breakdown = compute_wer("Augmentin 625 mg BD", "Augmentin 625 mg BD")
        assert wer == 0.0
        assert breakdown.total_edits == 0
        assert breakdown.reference_length == 4

    def test_both_empty_wer(self):
        wer, breakdown = compute_wer("", "")
        assert wer == 0.0
        assert breakdown.total_edits == 0

    def test_empty_reference_nonempty_hypothesis_wer(self):
        wer, breakdown = compute_wer("", "Paracetamol 500 mg")
        assert wer == 1.0
        assert breakdown.insertions == 3

    def test_single_word_substitution_wer(self):
        # 4 words, 1 substitution ("500mg" -> "650mg") -> WER = 1/4 = 0.25
        wer, breakdown = compute_wer(
            "Paracetamol 500 mg BD",
            "Paracetamol 650 mg BD",
        )
        assert pytest.approx(wer, 0.001) == 0.25
        assert breakdown.substitutions == 1
        assert breakdown.reference_length == 4

    def test_word_insertion_wer(self):
        # 3 words -> 4 words (1 insertion) -> WER = 1/3 = 0.3333
        wer, breakdown = compute_wer("Dolo 650 TDS", "Dolo 650 mg TDS")
        assert pytest.approx(wer, 0.001) == 0.3333
        assert breakdown.insertions == 1


class TestEvaluationNormalization:
    """Verifies deterministic evaluation text normalization."""

    def test_unicode_nfkc_normalization(self):
        # Fullwidth Latin characters decomposed and recomposed to standard ASCII
        fullwidth = "Ａｕｇｍｅｎｔｉｎ"
        norm = normalize_eval_text(fullwidth)
        assert norm == "augmentin"

    def test_whitespace_collapsing(self):
        messy = "  Paracetamol   \t\n  500   mg  \r\n"
        norm = normalize_eval_text(messy)
        assert norm == "paracetamol 500 mg"

    def test_case_folding(self):
        mixed = "MeTfOrMiN 500 MG 1-0-1 (BD)"
        norm = normalize_eval_text(mixed)
        assert norm == "metformin 500 mg 1-0-1 (bd)"


class TestClinicalEntityMetrics:
    """Verifies Precision, Recall, and F1 calculations for posology entities."""

    def test_perfect_entity_extraction(self):
        ground_truth = {
            "medicine_name": ["Augmentin", "Paracetamol"],
            "dosage": ["625 mg", "500 mg"],
            "frequency": ["1-0-1", "SOS"],
        }
        hypothesis = "Prescription: Augmentin 625 mg 1-0-1 and Paracetamol 500 mg SOS"
        metrics = compute_entity_metrics(ground_truth, hypothesis)

        assert metrics["medicine_name"]["precision"] == 1.0
        assert metrics["medicine_name"]["recall"] == 1.0
        assert metrics["medicine_name"]["f1"] == 1.0

        assert metrics["dosage"]["f1"] == 1.0
        assert metrics["frequency"]["f1"] == 1.0

    def test_partial_entity_extraction(self):
        ground_truth = {
            "medicine_name": ["Augmentin", "Paracetamol", "Pantocid"],
        }
        # Only Augmentin is present in hypothesis
        hypothesis = "Rx: Augmentin 625 mg"
        metrics = compute_entity_metrics(ground_truth, hypothesis)

        # 1 found out of 3 expected -> recall = 1/3 ~ 0.3333
        assert pytest.approx(metrics["medicine_name"]["recall"], 0.01) == 0.3333
        assert metrics["medicine_name"]["f1"] > 0.0

    def test_empty_ground_truth_returns_none(self):
        ground_truth = {"duration": []}
        hypothesis = "Augmentin 625 mg 5 days"
        metrics = compute_entity_metrics(ground_truth, hypothesis)

        assert metrics["duration"]["precision"] is None
        assert metrics["duration"]["recall"] is None
        assert metrics["duration"]["f1"] is None


class TestEvaluateOCRHypothesis:
    """Verifies complete EvaluationMetrics payload builder."""

    def test_evaluate_with_ground_truth(self):
        ref = "Augmentin 625 mg BD"
        hyp = "Augmentin 625 mg BD"
        metrics = evaluate_ocr_hypothesis(ref, hyp)

        assert metrics.cer == 0.0
        assert metrics.wer == 0.0
        assert metrics.char_edits is not None
        assert metrics.word_edits is not None

    def test_evaluate_without_ground_truth(self):
        metrics = evaluate_ocr_hypothesis(None, "Random OCR Text")
        assert metrics.cer is None
        assert metrics.wer is None
        assert metrics.char_edits is None
        assert metrics.word_edits is None
        assert metrics.entity_metrics is None
