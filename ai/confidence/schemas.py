"""
Pydantic Schemas for Phase 8: Confidence Estimation & Calibration.
Adheres strictly to PLAN.md Section 17:
- Explicit separation of Raw Model Signal from Calibrated Confidence
- Field-level confidence and multi-medicine independence
- Decoupling visual extraction confidence from reference correspondence
- Dosage confidence grounded in visual evidence, not reference overlap
- Preservation of conflicting signals and ambiguity
- Comprehensive calibration metrics and reliability diagram structures
"""

from typing import Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field

ConfidenceState = Literal["confident", "uncertain", "flagged"]
CalibrationStatus = Literal["calibrated", "uncalibrated", "insufficient_data", "not_available"]
CalibrationMethod = Literal["platt_scaling", "isotonic_regression", "temperature_scaling", "none"]


class RawConfidenceSignal(BaseModel):
    """
    Direct observational or algorithmic signal before probabilistic calibration.
    Must NEVER be presented as a calibrated posterior probability.
    """
    source: str = Field(
        ...,
        description="Source of the raw signal (e.g. 'multimodal_model_gemini', 'rag_retrieval_exact', 'visual_heuristics')"
    )
    raw_value: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Raw scalar score [0.0 - 1.0]. None if no quantitative score was produced."
    )
    signal_type: str = Field(
        ...,
        description="Category of signal (e.g. 'model_token_logprob_surrogate', 'retrieval_similarity', 'optical_clarity')"
    )
    model_version: Optional[str] = Field(
        None,
        description="Version/identifier of model that emitted the raw score"
    )
    config_version: Optional[str] = Field(
        None,
        description="Configuration version active when the signal was generated"
    )


class CalibratedConfidence(BaseModel):
    """
    Calibrated probability estimate resulting from a verified calibration transformation
    fitted against empirical ground-truth correctness outcomes.
    """
    value: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Empirically calibrated probability of correctness [0.0 - 1.0]. None if uncalibrated or data insufficient."
    )
    calibration_method: Optional[CalibrationMethod] = Field(
        None,
        description="Mathematical calibration function applied (e.g. 'platt_scaling', 'isotonic_regression')"
    )
    calibration_version: Optional[str] = Field(
        None,
        description="Version identifier of the calibration model artifact"
    )
    calibration_dataset_version: Optional[str] = Field(
        None,
        description="Version of the dataset used to calibrate this model"
    )
    calibration_status: CalibrationStatus = Field(
        "uncalibrated",
        description="Status of calibration: 'calibrated', 'uncalibrated', 'insufficient_data', or 'not_available'"
    )


class FieldConfidenceAssessment(BaseModel):
    """
    Confidence assessment for an individual posology field.
    Preserves raw signal, calibrated probability, visual support, and conflict flags.
    """
    field_name: str = Field(..., description="Posology field key (e.g. 'medicine_name', 'dosage', 'frequency', 'duration')")
    observed_value: Optional[str] = Field(None, description="Observed text value extracted from visual prescription")
    raw_signal: RawConfidenceSignal = Field(..., description="Uncalibrated raw model/retrieval score")
    calibrated: CalibratedConfidence = Field(..., description="Calibrated confidence representation")
    status: ConfidenceState = Field(..., description="Categorical certainty state: 'confident', 'uncertain', or 'flagged'")
    visual_evidence_supported: bool = Field(True, description="True if visual ink evidence supports this field extraction")
    reference_supported: Optional[bool] = Field(None, description="True if reference formulary supports this entity, if applicable")
    conflict_detected: bool = Field(False, description="True if visual extraction conflicts with validation or contextual evidence")
    conflict_description: Optional[str] = Field(None, description="Explanation of detected evidentiary conflict, if any")


class MedicineIdentityConfidence(BaseModel):
    """
    Explicit separation of visual handwriting extraction confidence
    from reference formulary correspondence confidence.
    Strong retrieval evidence must NEVER erase visual handwriting uncertainty.
    """
    visual_extraction_confidence: RawConfidenceSignal = Field(
        ...,
        description="Raw confidence from handwriting stroke interpretation in Phase 6"
    )
    reference_correspondence_confidence: Optional[RawConfidenceSignal] = Field(
        None,
        description="Retrieval similarity score against authoritative reference database from Phase 7"
    )
    combined_calibrated: Optional[CalibratedConfidence] = Field(
        None,
        description="Joint calibrated confidence if experimentally justified and fitted; otherwise None"
    )
    conflict_detected: bool = Field(
        False,
        description="True if visual extraction confidence is low but retrieval similarity is high (or vice-versa)"
    )
    conflict_note: Optional[str] = Field(
        None,
        description="Explicit documentation of discrepancy between visual clarity and nomenclature match"
    )


class DosageConfidenceAssessment(BaseModel):
    """
    Safety-critical dosage confidence assessment.
    Confidence in dosage MUST be grounded in visual handwriting evidence.
    Reference formulary matches must NOT artificially inflate dosage confidence.
    """
    observed_dosage: Optional[str] = Field(None, description="Extracted dosage string from visual prescription (immutable)")
    reference_strength: Optional[str] = Field(None, description="Documented strength in reference formulary, if matched")
    visual_extraction_confidence: RawConfidenceSignal = Field(..., description="Confidence that handwriting was read correctly")
    reference_support_status: Literal["matching", "mismatch", "not_in_reference", "unspecified"] = Field(
        "unspecified",
        description="Formulation compatibility between observed dosage and reference strength"
    )
    calibrated: CalibratedConfidence = Field(..., description="Calibrated confidence for dosage extraction")
    explanation: str = Field(..., description="Explanation of visual support and independence from reference strength")


class MedicineConfidenceAssessment(BaseModel):
    """
    Comprehensive confidence assessment for an individual medication line item.
    Ensures multi-medicine prescriptions evaluate each line item completely independently.
    """
    item_index: int = Field(..., ge=1, description="1-based index of medication line item")
    medicine_name: FieldConfidenceAssessment = Field(..., description="Confidence assessment for medicine candidate name")
    dosage: DosageConfidenceAssessment = Field(..., description="Safety-critical dosage confidence assessment")
    frequency: FieldConfidenceAssessment = Field(..., description="Confidence assessment for frequency / administration schedule")
    duration: FieldConfidenceAssessment = Field(..., description="Confidence assessment for treatment duration")
    abbreviations: List[str] = Field(default_factory=list, description="Clinical shorthand abbreviations observed")
    medicine_identity_confidence: MedicineIdentityConfidence = Field(..., description="Decoupled visual vs reference confidence")
    overall_raw_confidence: float = Field(..., ge=0.0, le=1.0, description="Composite raw score for this line item")
    overall_calibrated_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Calibrated confidence if available")
    calibration_status: CalibrationStatus = Field("uncalibrated", description="Line-item calibration status")
    conflict_flags: List[str] = Field(default_factory=list, description="Active conflict warning flags for this medication")


class PrescriptionConfidenceAssessment(BaseModel):
    """
    Top-level Phase 8 confidence estimation and calibration output for a prescription.
    Aggregates independent medication assessments and primary field assessments.
    """
    prescription_id: str = Field(..., description="Prescription identifier")
    medicines: List[MedicineConfidenceAssessment] = Field(
        default_factory=list,
        description="Independent confidence evaluations for each prescribed medicine"
    )
    fields: Dict[str, FieldConfidenceAssessment] = Field(
        default_factory=dict,
        description="Primary field-level confidence assessments matching Section 6 keys"
    )
    overall_raw_score: float = Field(..., ge=0.0, le=1.0, description="Document-level raw visual score")
    overall_calibrated_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Document-level calibrated probability if statistically valid calibration model exists"
    )
    calibration_status: CalibrationStatus = Field(
        "insufficient_data",
        description="Overall calibration status. 'insufficient_data' if sample size is too small for statistical calibration."
    )
    calibration_model_id: Optional[str] = Field(None, description="Identifier of calibration model artifact applied")
    calibration_method: Optional[str] = Field(None, description="Method applied (e.g. 'platt_scaling')")
    config_hash: str = Field(..., description="SHA-256 fingerprint of active confidence configuration")
    timestamp: str = Field(..., description="ISO 8601 evaluation timestamp")


class CalibrationBin(BaseModel):
    """
    Data point in a reliability diagram partition.
    Partitions confidence scores into intervals [lower_bound, upper_bound].
    """
    bin_index: int = Field(..., ge=0, description="0-based bin index")
    lower_bound: float = Field(..., ge=0.0, le=1.0, description="Inclusive or open lower bound")
    upper_bound: float = Field(..., ge=0.0, le=1.0, description="Inclusive upper bound")
    count: int = Field(..., ge=0, description="Number of prediction samples assigned to this bin")
    mean_confidence: float = Field(..., ge=0.0, le=1.0, description="Average predicted confidence of samples in this bin")
    empirical_accuracy: float = Field(..., ge=0.0, le=1.0, description="Empirical accuracy (fraction correct) of samples in this bin")
    calibration_gap: float = Field(..., ge=0.0, le=1.0, description="Absolute difference |empirical_accuracy - mean_confidence|")


class CalibrationMetrics(BaseModel):
    """
    Standard statistical calibration evaluation metrics.
    ECE, MCE, Brier score, and NLL computed strictly from empirical observations.
    """
    ece: float = Field(..., ge=0.0, le=1.0, description="Expected Calibration Error across bins")
    mce: float = Field(..., ge=0.0, le=1.0, description="Maximum Calibration Error across bins")
    brier_score: float = Field(..., ge=0.0, le=1.0, description="Brier Score (Mean Squared Error against binary ground truth)")
    nll: Optional[float] = Field(None, ge=0.0, description="Negative Log-Likelihood (log-loss)")
    sample_count: int = Field(..., ge=0, description="Number of evaluated samples")
    bin_count: int = Field(..., ge=1, description="Number of confidence partitions evaluated")
    bins: List[CalibrationBin] = Field(default_factory=list, description="Reliability diagram bin data")
    dataset_type: str = Field(
        "empirical_evaluation",
        description="Dataset classification: 'synthetic_verification' vs 'clinical_experimental'"
    )
    clinical_evidence: bool = Field(
        False,
        description="Explicit boolean: True only if derived from real clinical cohort"
    )


class CalibrationComparison(BaseModel):
    """
    Comparative assessment of calibration metrics before and after calibration transform.
    """
    uncalibrated_metrics: CalibrationMetrics = Field(..., description="Metrics evaluated on raw model scores")
    calibrated_metrics: Optional[CalibrationMetrics] = Field(None, description="Metrics evaluated on calibrated probabilities")
    ece_reduction: Optional[float] = Field(None, description="Absolute reduction in ECE (uncalibrated ECE - calibrated ECE)")
    evaluation_note: str = Field(..., description="Scientific note regarding sample size validity and statistical power")
    dataset_type: str = Field(
        "synthetic_verification",
        description="Dataset classification: explicitly flags whether evaluation is synthetic verification or clinical"
    )
    clinical_evidence: bool = Field(
        False,
        description="Strict boolean asserting whether metrics constitute clinical calibration evidence (strictly False for synthetic cohorts)"
    )


class CalibrationModelArtifact(BaseModel):
    """
    Versioned, auditable calibration model metadata and parameters.
    Stored as research artifacts with cryptographic hash verification.
    """
    calibration_model_id: str = Field(..., description="Unique model identifier (e.g. 'cal_platt_v1')")
    calibration_method: CalibrationMethod = Field(..., description="Calibration algorithm")
    calibration_version: str = Field(..., description="Model artifact release version (e.g. '1.0.0')")
    source_signal: str = Field(..., description="Description of the input signal calibrated")
    dataset_version: str = Field(..., description="Dataset split version used for fitting")
    sample_count: int = Field(..., ge=0, description="Number of training/calibration samples used")
    split_seed: int = Field(..., description="Random seed used for train/cal split partitioning")
    fit_timestamp: str = Field(..., description="ISO 8601 UTC timestamp of model fitting")
    configuration_hash: str = Field(..., description="SHA-256 hash of configuration")
    model_artifact_hash: str = Field(..., description="SHA-256 hash of serialized parameters")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Model parameters (e.g. slope, intercept, knots)")
    metrics: Optional[CalibrationMetrics] = Field(None, description="Calibration metrics achieved on calibration split")
