"""
OCR/HTR Evaluation Metrics (Section 10 & 11).
Computes Character Error Rate (CER), Word Error Rate (WER), Character Accuracy, and Word Accuracy
using exact dynamic programming Levenshtein distance with edit operation breakdown (S, D, I).
"""

import re
import unicodedata
from typing import Any, Dict, List, Optional, Sequence, Tuple


def normalize_eval_text(text: str) -> str:
    """
    Evaluation-only text normalization for CER/WER computation.
    Preserves raw text immutability.
    """
    if not text:
        return ""
    norm = unicodedata.normalize("NFKC", text)
    norm = norm.lower()
    norm = re.sub(r"[\r\n\t\u00a0\u2000-\u200b]+", " ", norm)
    norm = re.sub(r"\s+", " ", norm)
    return norm.strip()


def levenshtein_dp(ref: Sequence[Any], hyp: Sequence[Any]) -> Tuple[int, int, int, int]:
    """
    Levenshtein DP returning: (total_distance, substitutions, deletions, insertions)
    ref: Ground-truth reference sequence
    hyp: Predicted hypothesis sequence
    """
    m, n = len(ref), len(hyp)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref[i - 1] == hyp[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j - 1],  # Substitution
                    dp[i - 1][j],      # Deletion
                    dp[i][j - 1],      # Insertion
                )

    # Backtracking for operation counts
    i, j = m, n
    subs, dels, ins = 0, 0, 0
    while i > 0 or j > 0:
        if i > 0 and j > 0 and ref[i - 1] == hyp[j - 1]:
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

    return dp[m][n], subs, dels, ins


def compute_cer(reference: str, hypothesis: str, normalize: bool = True) -> Dict[str, Any]:
    """
    Computes Character Error Rate: CER = (S + D + I) / N
    """
    r_text = normalize_eval_text(reference) if normalize else reference
    h_text = normalize_eval_text(hypothesis) if normalize else hypothesis

    r_chars = list(r_text)
    h_chars = list(h_text)
    n_ref = len(r_chars)

    if n_ref == 0:
        if len(h_chars) == 0:
            return {"cer": 0.0, "char_accuracy": 1.0, "substitutions": 0, "deletions": 0, "insertions": 0, "ref_length": 0}
        else:
            return {"cer": float(len(h_chars)), "char_accuracy": 0.0, "substitutions": 0, "deletions": 0, "insertions": len(h_chars), "ref_length": 0}

    total_edits, subs, dels, ins = levenshtein_dp(r_chars, h_chars)
    cer = total_edits / n_ref
    char_acc = max(0.0, 1.0 - (subs + dels) / n_ref)

    return {
        "cer": round(cer, 4),
        "char_accuracy": round(char_acc, 4),
        "substitutions": subs,
        "deletions": dels,
        "insertions": ins,
        "ref_length": n_ref,
        "hyp_length": len(h_chars)
    }


def compute_wer(reference: str, hypothesis: str, normalize: bool = True) -> Dict[str, Any]:
    """
    Computes Word Error Rate: WER = (S + D + I) / N
    Tokenized on whitespace.
    """
    r_text = normalize_eval_text(reference) if normalize else reference
    h_text = normalize_eval_text(hypothesis) if normalize else hypothesis

    r_words = r_text.split() if r_text else []
    h_words = h_text.split() if h_text else []
    n_ref = len(r_words)

    if n_ref == 0:
        if len(h_words) == 0:
            return {"wer": 0.0, "word_accuracy": 1.0, "substitutions": 0, "deletions": 0, "insertions": 0, "ref_words": 0}
        else:
            return {"wer": float(len(h_words)), "word_accuracy": 0.0, "substitutions": 0, "deletions": 0, "insertions": len(h_words), "ref_words": 0}

    total_edits, subs, dels, ins = levenshtein_dp(r_words, h_words)
    wer = total_edits / n_ref
    word_acc = max(0.0, 1.0 - (subs + dels) / n_ref)

    return {
        "wer": round(wer, 4),
        "word_accuracy": round(word_acc, 4),
        "substitutions": subs,
        "deletions": dels,
        "insertions": ins,
        "ref_words": n_ref,
        "hyp_words": len(h_words)
    }
