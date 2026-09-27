"""
Phase 5: Reproducible OCR/HTR Evaluation Metrics
Implements exact Levenshtein DP algorithms for Character Error Rate (CER),
Word Error Rate (WER), and field-level entity metrics (Precision, Recall, F1).
Separates evaluation normalization from immutable raw OCR outputs.
"""

import re
import unicodedata
from typing import Any, Dict, List, Optional, Sequence, Tuple
from .schemas import EditBreakdown, EvaluationMetrics


def normalize_eval_text(text: str) -> str:
    """
    Standard evaluation normalization for CER and WER calculation.
    Rules:
    1. Unicode NFKC normalization
    2. Lowercase folding
    3. Collapse whitespace (tabs, newlines, spaces) to single space
    4. Strip leading and trailing whitespace
    CRITICAL: Never overwrite raw OCR text with this result.
    """
    if not text:
        return ""
    # 1. Unicode NFKC normalization
    norm = unicodedata.normalize("NFKC", text)
    # 2. Lowercase
    norm = norm.lower()
    # 3. Collapse whitespace
    norm = re.sub(r"[\r\n\t\u00a0\u2000-\u200b]+", " ", norm)
    norm = re.sub(r"\s+", " ", norm)
    return norm.strip()


def levenshtein_distance_dp(seq1: Sequence[Any], seq2: Sequence[Any]) -> Tuple[int, int, int, int]:
    """
    Computes exact Levenshtein edit distance with backtracked operation breakdown.
    seq1: Reference sequence (ground truth)
    seq2: Hypothesis sequence (prediction)
    Returns: (total_distance, substitutions, deletions, insertions)
    """
    m, n = len(seq1), len(seq2)
    # dp[i][j] stores the edit distance between seq1[:i] and seq2[:j]
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq1[i - 1] == seq2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j - 1],  # Substitution
                    dp[i - 1][j],      # Deletion from seq1
                    dp[i][j - 1],      # Insertion into seq1
                )

    # Backtrack to identify specific edit operations
    i, j = m, n
    subs = 0
    dels = 0
    ins = 0

    while i > 0 or j > 0:
        if i > 0 and j > 0 and seq1[i - 1] == seq2[j - 1]:
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            subs += 1
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            dels += 1
            i -= 1
        elif j > 0 and dp[i][j] == dp[i][j - 1] + 1:
            ins += 1
            j -= 1
        else:
            # Fallback path if multiple minimal edits exist
            if i > 0 and j > 0:
                subs += 1
                i -= 1
                j -= 1
            elif i > 0:
                dels += 1
                i -= 1
            else:
                ins += 1
                j -= 1

    total_edits = dp[m][n]
    return total_edits, subs, dels, ins


def compute_cer(
    reference: str,
    hypothesis: str,
    normalize: bool = True,
) -> Tuple[float, EditBreakdown]:
    """
    Computes Character Error Rate (CER):
    CER = (Substitutions + Deletions + Insertions) / len(reference)
    Handles empty reference/hypothesis safely without division-by-zero.
    """
    ref = normalize_eval_text(reference) if normalize else reference
    hyp = normalize_eval_text(hypothesis) if normalize else hypothesis

    ref_chars = list(ref)
    hyp_chars = list(hyp)

    ref_len = len(ref_chars)
    hyp_len = len(hyp_chars)

    if ref_len == 0 and hyp_len == 0:
        return 0.0, EditBreakdown(
            substitutions=0,
            deletions=0,
            insertions=0,
            reference_length=0,
            hypothesis_length=0,
            total_edits=0,
        )

    if ref_len == 0:
        return 1.0, EditBreakdown(
            substitutions=0,
            deletions=0,
            insertions=hyp_len,
            reference_length=0,
            hypothesis_length=hyp_len,
            total_edits=hyp_len,
        )

    total_edits, subs, dels, ins = levenshtein_distance_dp(ref_chars, hyp_chars)
    cer = float(total_edits) / float(ref_len)

    breakdown = EditBreakdown(
        substitutions=subs,
        deletions=dels,
        insertions=ins,
        reference_length=ref_len,
        hypothesis_length=hyp_len,
        total_edits=total_edits,
    )
    return cer, breakdown


def compute_wer(
    reference: str,
    hypothesis: str,
    normalize: bool = True,
) -> Tuple[float, EditBreakdown]:
    """
    Computes Word Error Rate (WER):
    WER = (Substitutions + Deletions + Insertions) / len(reference_words)
    Tokens are extracted by whitespace splitting on normalized text.
    """
    ref = normalize_eval_text(reference) if normalize else reference
    hyp = normalize_eval_text(hypothesis) if normalize else hypothesis

    ref_words = ref.split() if ref else []
    hyp_words = hyp.split() if hyp else []

    ref_len = len(ref_words)
    hyp_len = len(hyp_words)

    if ref_len == 0 and hyp_len == 0:
        return 0.0, EditBreakdown(
            substitutions=0,
            deletions=0,
            insertions=0,
            reference_length=0,
            hypothesis_length=0,
            total_edits=0,
        )

    if ref_len == 0:
        return 1.0, EditBreakdown(
            substitutions=0,
            deletions=0,
            insertions=hyp_len,
            reference_length=0,
            hypothesis_length=hyp_len,
            total_edits=hyp_len,
        )

    total_edits, subs, dels, ins = levenshtein_distance_dp(ref_words, hyp_words)
    wer = float(total_edits) / float(ref_len)

    breakdown = EditBreakdown(
        substitutions=subs,
        deletions=dels,
        insertions=ins,
        reference_length=ref_len,
        hypothesis_length=hyp_len,
        total_edits=total_edits,
    )
    return wer, breakdown


def compute_entity_metrics(
    ground_truth_entities: Dict[str, List[str]],
    hypothesis_text: str,
) -> Dict[str, Dict[str, Optional[float]]]:
    """
    Computes Precision, Recall, and F1 for clinical prescription entity categories:
    - medicine_name
    - dosage
    - frequency
    - duration
    Performs case-insensitive normalized substring/token verification.
    If ground truth entities are empty for a given category, values remain None (not fabricated).
    """
    hyp_norm = normalize_eval_text(hypothesis_text)
    results: Dict[str, Dict[str, Optional[float]]] = {}

    for field_name, expected_values in ground_truth_entities.items():
        if not expected_values:
            results[field_name] = {"precision": None, "recall": None, "f1": None}
            continue

        true_positives = 0
        total_expected = len(expected_values)

        for val in expected_values:
            val_norm = normalize_eval_text(val)
            if not val_norm:
                continue
            # Check presence via word boundary regex or substring in normalized hypothesis
            pattern = r"\b" + re.escape(val_norm) + r"\b"
            if re.search(pattern, hyp_norm) or val_norm in hyp_norm:
                true_positives += 1

        recall = float(true_positives) / float(total_expected) if total_expected > 0 else 0.0
        # For precision in raw OCR string, we treat matched items vs detected items
        precision = float(true_positives) / float(true_positives + (total_expected - true_positives)) if total_expected > 0 else 0.0
        f1 = (2.0 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        results[field_name] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }

    return results


def evaluate_ocr_hypothesis(
    reference_text: Optional[str],
    hypothesis_text: str,
    ground_truth_entities: Optional[Dict[str, List[str]]] = None,
) -> EvaluationMetrics:
    """
    Aggregates CER, WER, and entity metrics into an EvaluationMetrics schema.
    If reference_text is None, metrics remain None without fabrication.
    """
    if reference_text is None:
        return EvaluationMetrics(
            cer=None,
            wer=None,
            char_edits=None,
            word_edits=None,
            entity_metrics=None,
        )

    cer, char_breakdown = compute_cer(reference_text, hypothesis_text)
    wer, word_breakdown = compute_wer(reference_text, hypothesis_text)

    entity_metrics = None
    if ground_truth_entities:
        entity_metrics = compute_entity_metrics(ground_truth_entities, hypothesis_text)

    return EvaluationMetrics(
        cer=round(cer, 4),
        wer=round(wer, 4),
        char_edits=char_breakdown,
        word_edits=word_breakdown,
        entity_metrics=entity_metrics,
    )
