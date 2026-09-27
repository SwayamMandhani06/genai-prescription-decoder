"""
Phase 5: OCR/HTR Result Contracts and Evaluation Schemas
Enforces strict separation between immutable raw OCR output, normalized evaluation text,
and downstream metrics. Guarantees no confidence fabrication.
"""

from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Spatial bounding box coordinates for a detected word or line in pixels."""
    x: int = Field(..., ge=0, description="X coordinate of top-left corner in pixels")
    y: int = Field(..., ge=0, description="Y coordinate of top-left corner in pixels")
    width: int = Field(..., ge=0, description="Width of bounding box in pixels")
    height: int = Field(..., ge=0, description="Height of bounding box in pixels")


class OCRToken(BaseModel):
    """
    Token-level OCR extraction element.
    Preserves exact character string and bounding box.
    Confidence is Optional[float] and MUST be None if the engine does not provide a genuine score.
    """
    text: str = Field(..., description="Raw transcribed token text")
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="OCR engine confidence score [0.0 - 100.0]. Strictly None if unavailable; never fabricated.",
    )
    bbox: BoundingBox = Field(..., description="Spatial bounding box in pixels")
    line_num: Optional[int] = Field(None, description="Line sequence number within document block")
    block_num: Optional[int] = Field(None, description="Layout block index from OCR page segmentation")
    par_num: Optional[int] = Field(None, description="Paragraph index")
    word_num: Optional[int] = Field(None, description="Word index within current line")


class OCRLine(BaseModel):
    """Line-level aggregation of tokens preserving visual order."""
    line_num: int = Field(..., description="Document line index")
    text: str = Field(..., description="Concatenated tokens in line")
    tokens: List[OCRToken] = Field(default_factory=list, description="Ordered token list")
    bbox: Optional[BoundingBox] = Field(None, description="Enclosing bounding box of line")


class OCREngineMetadata(BaseModel):
    """Audit metadata describing the physical OCR engine and runtime parameters."""
    name: str = Field("tesseract", description="Engine name")
    version: str = Field(..., description="Actual detected engine binary version (e.g. 5.4.0.20240606)")
    language: str = Field("eng", description="Language data used during transcription")
    configuration_id: str = Field(..., description="Baseline configuration ID")
    configuration_hash: str = Field(..., description="Cryptographic SHA-256 of baseline configuration")
    psm: int = Field(..., description="Page segmentation mode parameter")
    oem: int = Field(..., description="OCR engine mode parameter")
    tessdata_path: Optional[str] = Field(None, description="Resolved path to language training models")


class OCRRunResult(BaseModel):
    """
    Primary OCR baseline run result contract.
    Contains strictly immutable raw OCR text, spatial tokens, and reproducibility hashes.
    """
    ocr_run_id: str = Field(..., description="Unique deterministic or UUID identifier for this OCR run")
    prescription_id: Optional[str] = Field(None, description="Traceable prescription ID if assigned")
    source_image_sha256: str = Field(..., description="SHA-256 hash of original untouched prescription image")
    preprocessing_artifact: str = Field(
        ...,
        description="Name of preprocessing representation used as OCR input (e.g. 'enhanced', 'grayscale')",
    )
    preprocessing_artifact_sha256: Optional[str] = Field(
        None,
        description="SHA-256 hash of derived preprocessed image fed to OCR engine",
    )
    engine: OCREngineMetadata = Field(..., description="Engine metadata and runtime parameters")
    raw_text: str = Field(..., description="Immutable raw OCR text exactly as produced by engine")
    raw_text_sha256: str = Field(..., description="SHA-256 hash of raw OCR text")
    tokens: List[OCRToken] = Field(default_factory=list, description="Extracted word tokens with boxes/confidence")
    lines: List[OCRLine] = Field(default_factory=list, description="Extracted lines of text")
    processing_status: Literal["completed", "partial", "failed"] = Field(
        ...,
        description="Processing status: completed (normal), partial (empty or minimal text), failed (error)",
    )
    duration_seconds: float = Field(..., ge=0.0, description="Execution duration in seconds")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of execution",
    )
    error_detail: Optional[str] = Field(None, description="Safe failure explanation if status is failed")


class NormalizedOCRRepresentation(BaseModel):
    """
    Separated normalized representation used exclusively for evaluation metrics.
    NEVER overwrites or replaces OCRRunResult.raw_text.
    """
    ocr_run_id: str = Field(..., description="Foreign reference to immutable OCRRunResult")
    raw_text: str = Field(..., description="Reference copy of immutable raw text")
    normalized_text: str = Field(..., description="Deterministic normalized text for evaluation")
    normalization_rules: List[str] = Field(
        default_factory=list,
        description="List of applied normalization rules (e.g. ['NFKC', 'lowercase', 'collapse_spaces'])",
    )
    tokens: List[str] = Field(default_factory=list, description="Normalized token sequence")


class EditBreakdown(BaseModel):
    """Granular Levenshtein edit distance breakdown."""
    substitutions: int = Field(0, ge=0)
    deletions: int = Field(0, ge=0)
    insertions: int = Field(0, ge=0)
    reference_length: int = Field(0, ge=0)
    hypothesis_length: int = Field(0, ge=0)
    total_edits: int = Field(0, ge=0)


class EvaluationMetrics(BaseModel):
    """Research evaluation metrics comparing OCR hypothesis against ground truth."""
    cer: Optional[float] = Field(None, ge=0.0, description="Character Error Rate (CER)")
    wer: Optional[float] = Field(None, ge=0.0, description="Word Error Rate (WER)")
    char_edits: Optional[EditBreakdown] = Field(None, description="Granular character edit breakdown")
    word_edits: Optional[EditBreakdown] = Field(None, description="Granular word edit breakdown")
    entity_metrics: Optional[Dict[str, Dict[str, Optional[float]]]] = Field(
        None,
        description="Entity Precision, Recall, F1 for fields (medicine_name, dosage, frequency, duration)",
    )


class BaselineExperimentRecord(BaseModel):
    """Complete serialized record of an OCR baseline experiment run."""
    experiment_id: str
    ocr_run_id: str
    sample_id: str
    source_image_sha256: str
    preprocessing_variant: str
    ocr_config_id: str
    raw_text: str
    normalized_text: str
    metrics: EvaluationMetrics
    processing_status: str
    duration_seconds: float
