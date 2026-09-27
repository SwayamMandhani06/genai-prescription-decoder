"""
Core Prescription Processing Schemas
Implements the central application contract specified in Section 6 and Section 11 of PLAN.md,
while preserving full compatibility with the Phase 1 frozen frontend client.
"""

from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field


# ==============================================================================
# 1. PLAN.md Section 6 Core Response Schemas
# ==============================================================================

class FieldExtractionItem(BaseModel):
    """
    Field-level interpretation adhering strictly to Section 6:
    value, confidence, and exactly one of (confident, uncertain, flagged).
    """
    value: str = Field(..., description="Normalized or extracted field text")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Calibrated confidence score [0.0 - 1.0]")
    status: Literal["confident", "uncertain", "flagged"] = Field(
        ..., description="Semantic certainty status: exactly one of confident, uncertain, flagged"
    )
    candidates: List[str] = Field(default_factory=list, description="Candidate interpretations considered")
    explanation: Optional[str] = Field(None, description="Clinical rationale for the interpretation")
    uncertainty_reason: Optional[str] = Field(None, description="Explicit clinical reason for uncertainty (WHY)")
    verification_instruction: Optional[str] = Field(None, description="Actionable instruction for human review (WHAT TO DO)")


class LasaFlagItem(BaseModel):
    """
    Look-Alike Sound-Alike (LASA) conflict flag adhering to Section 6.
    """
    field: str = Field(..., description="Target field key (e.g. medicine_name)")
    conflict_with: str = Field(..., description="Conflicting drug entity (e.g. Metronidazole)")
    risk: Literal["low", "medium", "high"] = Field(..., description="Calibrated clinical risk level")
    similarity_score: Optional[float] = Field(None, description="Similarity percentage score [0 - 100]")
    tall_man_prescribed: Optional[str] = Field(None, description="ISMP Tall Man prescribed name")
    tall_man_confused: Optional[str] = Field(None, description="ISMP Tall Man confused counterpart")
    details: Optional[str] = Field(None, description="Clinical explanation of pharmacological consequence")


class ValidationItem(BaseModel):
    """
    Formulary / reference database validation record adhering to Section 6.
    """
    found_in_db: bool = Field(..., description="True if grounded in authoritative formulary")
    source: str = Field(..., description="Evidence authority (e.g. CDSCO, RxNorm)")
    matched_entity_name: Optional[str] = Field(None, description="Canonical matched drug entity")
    generic_salt: Optional[str] = Field(None, description="Generic active pharmaceutical ingredient")
    rxnorm_cui: Optional[str] = Field(None, description="NLM RxNorm Concept Unique Identifier")
    cdsco_schedule: Optional[str] = Field(None, description="Indian CDSCO Schedule classification")


class MultilingualSummary(BaseModel):
    """
    Patient-friendly multilingual summary strings in English, Hindi, and Marathi.
    """
    en: str = Field(..., description="English explanation")
    hi: str = Field(..., description="Hindi explanation")
    mr: str = Field(..., description="Marathi explanation")


# ==============================================================================
# 2. Phase 1 Frontend Visual Envelope Models (Bounding Boxes, Telemetry, etc.)
# ==============================================================================

class BoundingBox(BaseModel):
    x: float = Field(..., description="X coordinate percentage [0 - 100]")
    y: float = Field(..., description="Y coordinate percentage [0 - 100]")
    width: float = Field(..., description="Width percentage [0 - 100]")
    height: float = Field(..., description="Height percentage [0 - 100]")


class ExtractedEntity(BaseModel):
    field_key: Literal["medicine_name", "dosage", "frequency", "duration", "abbreviation"]
    field_label: str
    raw_value: str
    normalized_value: str
    confidence: float
    status: Literal["confident", "uncertain", "flagged", "abstained"]
    stroke_source: str
    bounding_box: BoundingBox
    explanation: str
    uncertainty_reason: Optional[str] = None
    verification_instruction: Optional[str] = None
    interpreted_candidate: Optional[str] = None


class AlternativeCandidate(BaseModel):
    name: str
    generic: str
    similarity_score: float
    notes: str


class ValidationEvidence(BaseModel):
    candidate_name: str
    matched_entity_name: str
    generic_salt: str
    validation_status: Literal["cdsco_approved", "rxnorm_grounded", "formulary_match", "unverified"]
    status_badge_text: str
    cdsco_schedule: str
    rxnorm_cui: str
    atc_code: str
    therapeutic_class: str
    indications: str
    evidence_source: str
    reference_url: Optional[str] = None
    alternatives: List[AlternativeCandidate] = Field(default_factory=list)


class LasaScreening(BaseModel):
    has_warning: bool
    prescribed_candidate: str
    confusable_counterpart: str
    tall_man_prescribed: str
    tall_man_confused: str
    similarity_score: float
    similarity_type: Literal["Orthographic & Phonetic", "Orthographic", "Phonetic"]
    metaphone_match: bool
    clinical_risk_summary: str
    mandated_action: str


class PosologyTimingSlot(BaseModel):
    time_slot: str
    icon_key: str
    dosage_label: str
    food_instruction: str


class PosologyLanguagePack(BaseModel):
    summary: str
    patient_instructions: str
    daily_schedule: List[PosologyTimingSlot]
    precautions: List[str]


class MultilingualPosology(BaseModel):
    en: PosologyLanguagePack
    hi: PosologyLanguagePack
    mr: PosologyLanguagePack


class DocumentTelemetry(BaseModel):
    estimated_dpi: int
    contrast_ratio: float
    skew_angle_deg: float
    illegibility_score: float
    orientation: Literal["Portrait", "Landscape", "Square"]


class PrescriptionMetadata(BaseModel):
    request_id: str
    timestamp: str
    processing_time_ms: int
    model_version: str
    pipeline_stages_completed: int


class PatientInfo(BaseModel):
    name: str
    age_gender: str


class PrescriberInfo(BaseModel):
    name: str
    qualifications: str
    registration_no: str
    clinic_name: str
    clinic_address: str


class PrescriptionData(BaseModel):
    accession_id: str
    script_sample_key: str
    scenario_title: str
    scenario_subtitle: str
    difficulty_tag: Literal["Clear Handwriting", "Moderate Cursive", "LASA Similarity", "Severe Ambiguity"]
    overall_status: Literal["VERIFIED", "NEEDS_VERIFICATION", "SAFETY_ALERT", "SELECTIVE_ABSTAIN", "ABSTAINED"]
    document_confidence: float
    patient_info: PatientInfo
    prescriber_info: PrescriberInfo
    extracted_entities: List[ExtractedEntity]
    validation_evidence: ValidationEvidence
    lasa_screening: LasaScreening
    posology_explanation: MultilingualPosology


# ==============================================================================
# 3. Complete Dual-Contract Response
# ==============================================================================

class PrescriptionAnalyzeResponse(BaseModel):
    """
    Complete Response Model:
    Contains both the PLAN.md Section 6 Contract and the Phase 1 UI Envelope,
    extended with Phase 4 preprocessed image reference and quality assessment metadata.
    """
    # PLAN.md Section 6 Standard Top-Level Contract:
    prescription_id: str = Field(..., description="Statutory unique prescription tracking identifier")
    original_image_url: str = Field(..., description="Preserved accessible URL for the uploaded prescription image")
    fields: Dict[str, FieldExtractionItem] = Field(..., description="Field-level dictionary conforming to Section 6")
    lasa_flags: List[LasaFlagItem] = Field(default_factory=list, description="Array of detected LASA risk flags")
    validation: Dict[str, ValidationItem] = Field(default_factory=dict, description="Validation evidence dictionary")
    explanation: MultilingualSummary = Field(..., description="Multilingual patient instructions (EN, HI, MR)")
    requires_human_review: bool = Field(False, description="True if clinician or pharmacist review is mandated")

    # Phase 1 Frontend UI Data Envelope:
    status: Literal["success", "abstain", "error"] = Field("success", description="Overall execution status")
    meta: PrescriptionMetadata = Field(..., description="Pipeline execution metadata and request ID")
    document_telemetry: DocumentTelemetry = Field(..., description="Pre-flight image quality metrics")
    data: PrescriptionData = Field(..., description="Detailed clinical and spatial posology dataset")

    # Phase 4 Preprocessing & Quality Infrastructure Extensions (PLAN.md Section 13):
    processed_image_url: Optional[str] = Field(
        None,
        description="Preserved accessible URL for the primary derived preprocessed image (enhanced representation)"
    )
    quality_report: Optional[Dict[str, Any]] = Field(
        None,
        description="Phase 4 image quality assessment report containing optical metrics and tri-state decision"
    )
    preprocessing_manifest: Optional[Dict[str, Any]] = Field(
        None,
        description="Phase 4 derived artifacts manifest and cryptographic SHA-256 fingerprints"
    )

    # Phase 6 Multimodal Vision-Language Extraction Extensions:
    medicines: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Phase 6 structured multi-medicine extractions with field-level uncertainty and visual evidence"
    )
    multimodal_result: Optional[Dict[str, Any]] = Field(
        None,
        description="Phase 6 complete PrescriptionExtractionResult including model audit metadata and raw traceability"
    )

    # Phase 7 RAG Medicine Validation Extensions (PLAN.md Section 16):
    medicine_validations: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Phase 7 evidence-grounded medicine validation results, retrieval candidates, and provenance"
    )


