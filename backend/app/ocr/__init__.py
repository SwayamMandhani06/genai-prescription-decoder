"""
Phase 5: Conventional OCR/HTR Research Baseline Module
Exposes configuration, schemas, engine adapter, baseline service, and reproducible metrics.
"""

from .config import OCRBaselineConfig, find_default_tesseract_cmd
from .engine import TesseractEngine
from .metrics import (
    compute_cer,
    compute_wer,
    compute_entity_metrics,
    evaluate_ocr_hypothesis,
    normalize_eval_text,
    levenshtein_distance_dp,
)
from .schemas import (
    BoundingBox,
    EditBreakdown,
    EvaluationMetrics,
    NormalizedOCRRepresentation,
    OCREngineMetadata,
    OCRLine,
    OCRRunResult,
    OCRToken,
    BaselineExperimentRecord,
)
from .service import OCRBaselineService

__all__ = [
    "OCRBaselineConfig",
    "find_default_tesseract_cmd",
    "TesseractEngine",
    "OCRBaselineService",
    "OCRRunResult",
    "OCRToken",
    "OCRLine",
    "BoundingBox",
    "OCREngineMetadata",
    "NormalizedOCRRepresentation",
    "EditBreakdown",
    "EvaluationMetrics",
    "BaselineExperimentRecord",
    "compute_cer",
    "compute_wer",
    "compute_entity_metrics",
    "evaluate_ocr_hypothesis",
    "normalize_eval_text",
    "levenshtein_distance_dp",
]
