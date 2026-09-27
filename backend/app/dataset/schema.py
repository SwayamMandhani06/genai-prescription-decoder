"""
Ground Truth Annotation and Document Schemas (Phase 3)
Strictly distinguishes ground truth, derived annotations, model predictions, and human review labels.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator


class AnnotationTier(str, Enum):
    """Tier of annotation indicating provenance and authority."""
    GROUND_TRUTH = "ground_truth"          # Expert transcription verified against physical ink
    DERIVED = "derived"                    # Deterministically expanded or mapped (e.g. RxNorm code)
    MODEL_PREDICTION = "model_prediction"  # Output from an AI model (reserved for Phase 6+)
    HUMAN_REVIEW = "human_review"          # Adjudicated or corrected by clinical review


class AmbiguityLevel(str, Enum):
    """Assessment of cursive or stroke legibility in handwriting."""
    NONE = "none"                          # Clear, unambiguous print or distinct cursive
    MINOR = "minor"                        # Minor ligature ambiguity resolvable via clinical context
    SEVERE_ILLEGIBLE = "severe_illegible"  # Severe stroke collapse requiring clinical abstention


class BoundingBox(BaseModel):
    """Normalized spatial coordinates [0.0 - 1.0] referencing the prescription image."""
    x: float = Field(..., ge=0.0, le=1.0, description="Top-left X coordinate normalized")
    y: float = Field(..., ge=0.0, le=1.0, description="Top-left Y coordinate normalized")
    width: float = Field(..., gt=0.0, le=1.0, description="Bounding box width normalized")
    height: float = Field(..., gt=0.0, le=1.0, description="Bounding box height normalized")

    @model_validator(mode="after")
    def check_bounds(self) -> "BoundingBox":
        if self.x + self.width > 1.001:
            raise ValueError(f"Bounding box extends beyond right edge: x={self.x} + width={self.width} > 1.0")
        if self.y + self.height > 1.001:
            raise ValueError(f"Bounding box extends beyond bottom edge: y={self.y} + height={self.height} > 1.0")
        return self


class MedicationEntityAnnotation(BaseModel):
    """Ground truth annotation for a single prescribed medication line item."""
    item_index: int = Field(..., ge=1, description="1-based index of medication on the prescription pad")
    raw_text: str = Field(..., min_length=1, description="Exact transcription of handwritten doctor ink")
    medicine_name: str = Field(..., min_length=1, description="Standardized trade or generic medicine name")
    dosage_strength: Optional[str] = Field(None, description="Dosage and strength (e.g. '625 mg', '500 mg')")
    frequency: Optional[str] = Field(None, description="Prescribed frequency notation (e.g. '1-0-1', 'TDS', 'OD')")
    duration: Optional[str] = Field(None, description="Duration of therapy (e.g. '5 days', '1 month')")
    route: Optional[str] = Field("Oral", description="Route of administration (e.g. 'Oral', 'Topical', 'IV')")
    instructions: Optional[str] = Field(None, description="Patient posology instructions (e.g. 'After food')")
    abbreviations: List[str] = Field(default_factory=list, description="Clinical shorthand tokens present (e.g. ['BD', 'PC'])")
    ambiguity_level: AmbiguityLevel = Field(default=AmbiguityLevel.NONE, description="Visual ambiguity classification")
    is_lasa_risk: bool = Field(default=False, description="True if drug belongs to an ISMP/FDA confusable pair")
    bounding_box: Optional[BoundingBox] = Field(None, description="Spatial coordinates on document canvas")


class GroundTruthAnnotation(BaseModel):
    """
    Gold-standard ground truth annotation for a complete prescription document.
    Must never be mixed with model predictions.
    """
    tier: AnnotationTier = Field(default=AnnotationTier.GROUND_TRUTH, description="Must be 'ground_truth'")
    document_id: str = Field(..., min_length=3, description="Canonical document identifier (e.g. 'DOC-RX-001')")
    image_rel_path: str = Field(..., min_length=3, description="Relative path from data root to image")
    image_sha256: str = Field(..., min_length=64, max_length=64, description="SHA-256 cryptographic checksum of image")
    patient_deidentified: bool = Field(..., description="Certification that no real patient PII is contained")
    language_script: str = Field(default="Latin", description="Primary writing script ('Latin', 'Devanagari', etc.)")
    medications: List[MedicationEntityAnnotation] = Field(default_factory=list, description="Prescribed medications list")
    clinical_department: Optional[str] = Field("General Medicine", description="Specialty department of prescription")
    source_dataset_id: str = Field(..., description="ID referencing dataset manifest source entry")

    @field_validator("tier")
    @classmethod
    def validate_tier_is_ground_truth(cls, v: AnnotationTier) -> AnnotationTier:
        if v != AnnotationTier.GROUND_TRUTH:
            raise ValueError(f"GroundTruthAnnotation must strictly have tier='ground_truth', received '{v}'")
        return v

    @field_validator("patient_deidentified")
    @classmethod
    def validate_privacy(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Safety violation: patient_deidentified must be True before inclusion in dataset")
        return v


class DerivedAnnotation(BaseModel):
    """
    Derived posology and ontological enrichment data linked to a ground truth record.
    Clearly decoupled from raw ground truth ink transcription.
    """
    tier: AnnotationTier = Field(default=AnnotationTier.DERIVED, description="Must be 'derived'")
    document_id: str = Field(..., description="Foreign key to GroundTruthAnnotation.document_id")
    medication_index: int = Field(..., ge=1, description="Reference to MedicationEntityAnnotation.item_index")
    canonical_rxnorm_cui: Optional[str] = Field(None, description="RxNorm Concept Unique Identifier")
    canonical_cdsco_name: Optional[str] = Field(None, description="Standard CDSCO gazette active substance name")
    expanded_instructions_en: Optional[str] = Field(None, description="Normalized English posology instructions")
    expanded_instructions_hi: Optional[str] = Field(None, description="Hindi vernacular translation")
    expanded_instructions_mr: Optional[str] = Field(None, description="Marathi vernacular translation")
    enrichment_method: str = Field(default="deterministic_rule_based", description="Methodology used to derive fields")


class PrescriptionDocumentRecord(BaseModel):
    """Master record encapsulating a prescription document, ground truth, and derived annotations."""
    document_id: str = Field(..., description="Unique document ID")
    patient_group_id: str = Field(..., description="Patient or physician grouping key to prevent split leakage")
    ground_truth: GroundTruthAnnotation = Field(..., description="Gold-standard ground truth")
    derived_annotations: List[DerivedAnnotation] = Field(default_factory=list, description="Associated derived data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Heuristic, split, and provenance metadata")
