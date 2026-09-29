"""
Evaluation OCR Package Exports.
"""

from eval.ocr.metrics import compute_cer, compute_wer, normalize_eval_text
from eval.ocr.evaluator import OCREvaluator

__all__ = [
    "compute_cer",
    "compute_wer",
    "normalize_eval_text",
    "OCREvaluator"
]
