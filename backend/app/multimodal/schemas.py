"""
Phase 6: Multimodal Vision-Language Extraction Schemas
Typed data contracts for multimodal prescription extraction, field uncertainty,
visual evidence grounding, and multi-medicine representations.
"""

from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field

FieldStatus = Literal["confident", "uncertain", "flagged"]
FieldPresence = Literal["present", "absent"]
ExtractionState = Literal["extracted", "ambiguous", "missing"]
EvidenceType = Literal["visual_region", "image_level"]
EvidenceSource = Literal["original_image", "preprocessed_image"]


class BoundingBox(BaseModel):
    """Spatial bounding box coordinates expressed as normalized percentage [0 - 100]."""
    x: float = Field(..., ge=0.0, le=100.0, description="X coordinate of top-left corner percentage")
    y: float = Field(..., ge=0.0, le=100.0, description="Y coordinate of top-left corner percentage")
    width: float = Field(..., ge=0.0, le=100.0, description="Width percentage")
    height: float = Field(..., ge=0.0, le=100.0, description="Height percentage")


class VisualEvidence(BaseModel):
    """
    Evidence grounding describing where the visual support originated.
    Uses 'image_level' when coordinates cannot be determined reliably without fabrication.
    """
    source: EvidenceSource = Field(
        "original_image",
        description="Source visual artifact ('original_image' or 'preprocessed_image')",
    )
    evidence_type: EvidenceType = Field(
        "image_level",
        description="Grounding granularity: 'visual_region' (if bounded) or 'image_level' (whole document)",
    )
    region: Optional[BoundingBox] = Field(
        None,
        description="Spatial bounding box in percentage [0 - 100]. None if evidence_type is image_level.",
    )
    note: Optional[str] = Field(
        None,
        description="Observational visual note describing ink stroke or layout context",
    )


class ExtractedField(BaseModel):
    """
    Field-level extraction element adhering strictly to Phase 6 semantic distinctions:
    - MISSING / ABSENT: The field is not present in the prescription or cannot be located
      (presence='absent', extraction_state='missing', value=None).
    - UNCERTAIN: The field appears to be present, but the visual content cannot be reliably determined
      (presence='present', extraction_state='ambiguous', status='uncertain').
    - CONFIDENT: The field is visually supported with sufficient extraction certainty for Phase 6 output
      (presence='present', extraction_state='extracted', status='confident').
    - FLAGGED: The extraction requires explicit review or escalation (status='flagged').
    """
    value: Optional[str] = Field(
        None,
        description="Extracted field value as visually observed. None if field is missing/absent or cannot be located.",
    )
    status: FieldStatus = Field(
        "confident",
        description="Semantic certainty status: strictly one of confident, uncertain, flagged",
    )
    presence: FieldPresence = Field(
        "present",
        description=(
            "Explicit field presence: 'present' if the field appears in the prescription, "
            "'absent' if the field is not present in the prescription or cannot be located."
        ),
    )
    extraction_state: ExtractionState = Field(
        "extracted",
        description=(
            "Fine-grained extraction state: 'extracted' (confident visual match), "
            "'ambiguous' (field present but visual content cannot be reliably determined), "
            "'missing' (field is not present in the prescription or cannot be located)."
        ),
    )
    evidence: Optional[VisualEvidence] = Field(
        None,
        description="Visual evidence traceability linking field to image",
    )
    candidates: List[str] = Field(
        default_factory=list,
        description="Plausible candidate interpretations when visual evidence is ambiguous",
    )
    explanation: Optional[str] = Field(
        None,
        description="Observational visual explanation",
    )
    uncertainty_reason: Optional[str] = Field(
        None,
        description="Explicit visual reason for uncertainty when content is ambiguous (null for absent fields)",
    )
    verification_instruction: Optional[str] = Field(
        None,
        description="Actionable verification instruction for human reviewer",
    )


class ExtractedMedicine(BaseModel):
    """
    Structured extraction representation for an individual prescribed medication line item.
    Supports single or multiple prescribed medicines without merging distinct items.
    """
    medicine_name: ExtractedField = Field(..., description="Prescribed medicine brand or generic candidate")
    dosage: ExtractedField = Field(..., description="Prescribed dosage strength and unit (e.g. '500 mg')")
    frequency: ExtractedField = Field(..., description="Prescribed administration schedule (e.g. '1-0-1', 'BD')")
    duration: ExtractedField = Field(..., description="Prescribed treatment duration (e.g. '5 days')")
    abbreviations: List[str] = Field(
        default_factory=list,
        description="Preserved posology abbreviations exactly as visually observed (e.g. ['BD', 'PC'])",
    )
    status: FieldStatus = Field(
        "confident",
        description="Overall certainty status for this medication line item",
    )
    overall_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Raw model confidence signal if available. Strictly uncalibrated at Phase 6.",
    )
    evidence: Optional[VisualEvidence] = Field(
        None,
        description="Line-level visual region bounding box or image evidence",
    )
    candidates: List[str] = Field(
        default_factory=list,
        description="Alternative candidate drug names observed in cursive ink strokes",
    )


class ModelMetadata(BaseModel):
    """Audit metadata describing the multimodal vision-language model used for extraction."""
    provider: str = Field(..., description="Model provider ('gemini' or 'mock')")
    model_id: str = Field(..., description="Model identifier (e.g. 'gemini-3.8-flash')")
    model_version: str = Field(..., description="Specific model release version")
    prompt_version: str = Field(..., description="Clinical extraction prompt version")
    config_version: str = Field(..., description="Multimodal configuration version")
    is_mock: bool = Field(False, description="True if output was produced by deterministic test adapter")


class PrescriptionExtractionResult(BaseModel):
    """
    Primary Phase 6 multimodal prescription extraction contract.
    Contains structured multi-medicine extractions, field-level uncertainty, and evidence grounding.
    """
    prescription_id: str = Field(..., description="Statutory prescription tracking identifier")
    original_image_url: str = Field(..., description="Preserved accessible URL of uploaded original image")
    source_image_sha256: str = Field(..., description="Cryptographic SHA-256 of original untouched image")
    preprocessed_image_url: Optional[str] = Field(None, description="Accessible URL of Phase 4 preprocessed image")
    preprocessed_image_sha256: Optional[str] = Field(None, description="SHA-256 of derived preprocessed image")
    model: ModelMetadata = Field(..., description="Audit metadata for model and prompt")
    medicines: List[ExtractedMedicine] = Field(
        default_factory=list,
        description="List of independently extracted prescribed medications",
    )
    fields: Dict[str, ExtractedField] = Field(
        default_factory=dict,
        description="Aggregate primary field dictionary matching PLAN.md Section 6 schema",
    )
    requires_human_review: bool = Field(
        False,
        description="True if any extracted field or medication exhibits uncertainty or missing posology",
    )
    raw_model_response: Optional[str] = Field(
        None,
        description="Raw serialized response text from model for scientific auditability",
    )
    duration_seconds: float = Field(..., ge=0.0, description="Inference latency in seconds")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of extraction",
    )
