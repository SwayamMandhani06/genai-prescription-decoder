"""
Phase 10: LASA (Look-Alike / Sound-Alike) Detection Schemas.
Typed contracts for:
- Individual LASA similarity comparisons
- Medicine-level LASA screening results
- Prescription-level LASA detection output
- Provenance and audit metadata

Strictly a safety-oriented similarity conflict detector:
- Does NOT diagnose, prescribe, or assess clinical danger/adverse drug event probabilities.
- "Risk" or conflict level denotes lexical/phonetic similarity severity, NOT clinical risk.
- Flags for downstream Phase 9 verification consumption.
- Medicine identity only — dosage/strength is out of scope.
"""

from typing import Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field, model_validator

# Similarity / Conflict Severity Level:
# Represents name-similarity collision severity (low, medium, high) based on orthographic,
# phonetic, and curated confusable pair thresholds.
# This is an application-level conflict severity classification, NOT a clinical risk assessment,
# medical risk probability, adverse event forecast, or dispensing diagnosis.
LasaRiskLevel = Literal["low", "medium", "high"]
SimilarityType = Literal["orthographic", "phonetic", "combined", "known_pair"]
LasaExecutionStatus = Literal["completed", "failed", "unavailable"]


class LasaSimilarityDetail(BaseModel):
    """
    Granular similarity measurement between a prescribed candidate
    and a single confusable counterpart.
    """
    confusable_name: str = Field(
        ...,
        description="Reference medicine name that could be confused with the prescribed candidate",
    )
    confusable_reference_id: Optional[str] = Field(
        None,
        description="Reference ID from RAG index (if matched)",
    )
    confusable_generic_name: Optional[str] = Field(
        None,
        description="Generic/salt name of the confusable medicine (if known from reference data)",
    )
    orthographic_score: float = Field(
        ...,
        ge=0.0, le=1.0,
        description="SequenceMatcher ratio between normalized names [0.0-1.0]",
    )
    phonetic_score: float = Field(
        ...,
        ge=0.0, le=1.0,
        description="Phonetic similarity ratio (Double Metaphone codes) [0.0-1.0]",
    )
    combined_score: float = Field(
        ...,
        ge=0.0, le=1.0,
        description="Weighted combined similarity score [0.0-1.0]",
    )
    metaphone_match: bool = Field(
        ...,
        description="True if primary Double Metaphone codes are identical",
    )
    similarity_type: SimilarityType = Field(
        ...,
        description="Dominant similarity mechanism that triggered the flag",
    )
    risk_level: LasaRiskLevel = Field(
        ...,
        description=(
            "Similarity conflict severity classification based on configured thresholds. "
            "Denotes lexical/phonetic proximity, NOT a clinical risk assessment or adverse event forecast."
        ),
    )
    is_known_pair: bool = Field(
        False,
        description="True if this pair is in the curated ISMP/high-risk LASA pairs list",
    )
    tall_man_prescribed: Optional[str] = Field(
        None,
        description="ISMP Tall Man Lettering for the prescribed candidate (if known pair)",
    )
    tall_man_confused: Optional[str] = Field(
        None,
        description="ISMP Tall Man Lettering for the confusable counterpart (if known pair)",
    )
    clinical_context: str = Field(
        ...,
        description=(
            "Traceable rationale explaining why this pair was flagged based on name similarity. "
            "This is an application safety-review state indicating that a potential medicine-name "
            "conflict requires attention/verification. It does NOT assert clinical danger, "
            "adverse drug event, wrong medicine, medical risk probability, diagnosis, or prescribing recommendation."
        ),
    )


class MedicineLasaResult(BaseModel):
    """
    LASA screening result for a single extracted medicine candidate.
    """
    item_index: int = Field(..., ge=1, description="1-based index of medication line item")
    prescribed_candidate: str = Field(
        ...,
        description="Extracted medicine name from Phase 6",
    )
    normalized_candidate: str = Field(
        ...,
        description="Normalized form of the prescribed candidate",
    )
    status: LasaExecutionStatus = Field(
        "completed",
        description="Execution status of screening for this medicine ('completed', 'failed', 'unavailable')",
    )
    has_lasa_conflict: Optional[bool] = Field(
        None,
        description="True if at least one confusable counterpart exceeded thresholds; False if screened and none detected; None if failed/unavailable",
    )
    highest_risk: LasaRiskLevel = Field(
        "low",
        description="Maximum similarity conflict severity level among all detected confusable counterparts (not a clinical risk assessment)",
    )
    confusable_count: int = Field(
        0,
        ge=0,
        description="Number of confusable counterparts detected",
    )
    confusables: List[LasaSimilarityDetail] = Field(
        default_factory=list,
        description="Ordered list of confusable counterparts (descending by combined_score)",
    )
    top_confusable_name: Optional[str] = Field(
        None,
        description="Name of the highest-scoring confusable counterpart (convenience field)",
    )
    top_confusable_score: Optional[float] = Field(
        None,
        ge=0.0, le=1.0,
        description="Combined similarity score of the highest-scoring confusable",
    )
    error_message: Optional[str] = Field(
        None,
        description="Error or unavailability details if status != 'completed'",
    )

    @model_validator(mode="before")
    @classmethod
    def sync_status_and_conflict(cls, data: Any) -> Any:
        if isinstance(data, dict):
            status = data.get("status", "completed")
            conflict = data.get("has_lasa_conflict")
            if status != "completed" and conflict is False:
                # Never report conflict_detected=False when detection did not complete
                data["has_lasa_conflict"] = None
        return data


class LasaDetectionProvenance(BaseModel):
    """
    Audit metadata for reproducibility of LASA detection.
    """
    policy_version: str = Field(..., description="LASA policy version")
    config_hash: str = Field(..., description="SHA-256 fingerprint of active LASA configuration")
    orthographic_threshold: float = Field(..., description="Active orthographic threshold")
    phonetic_threshold: float = Field(..., description="Active phonetic threshold")
    combined_threshold: float = Field(..., description="Active combined threshold")
    reference_pool_size: int = Field(
        ...,
        description="Number of reference medicines in the candidate pool for comparison",
    )
    known_pairs_count: int = Field(
        ...,
        description="Number of curated Tall Man pairs in the active configuration",
    )
    timestamp: str = Field(..., description="ISO 8601 detection timestamp")


class PrescriptionLasaDetection(BaseModel):
    """
    Prescription-level LASA detection result consolidating all medicine-level screenings.
    """
    prescription_id: str = Field(..., description="Prescription tracking identifier")
    status: LasaExecutionStatus = Field(
        "completed",
        description="Overall execution status of LASA screening ('completed', 'failed', 'unavailable')",
    )
    conflict_detected: Optional[bool] = Field(
        None,
        description=(
            "True if any medicine has a conflict; False if screening completed and no conflict detected; "
            "None if screening failed or was unavailable."
        ),
    )
    has_any_lasa_conflict: Optional[bool] = Field(
        None,
        description="Backward-compatible alias for conflict_detected",
    )
    highest_risk: LasaRiskLevel = Field(
        "low",
        description="Maximum similarity conflict severity across all medicines (not a clinical risk assessment)",
    )
    total_medicines_screened: int = Field(
        0,
        ge=0,
        description="Total number of medicines evaluated for LASA conflicts",
    )
    medicines_with_conflicts: int = Field(
        0,
        ge=0,
        description="Number of medicines that have at least one LASA flag",
    )
    medicines: List[MedicineLasaResult] = Field(
        default_factory=list,
        description="Per-medicine LASA screening results",
    )
    summary: str = Field(
        ...,
        description="Human-readable summary of LASA detection findings",
    )
    provenance: LasaDetectionProvenance = Field(
        ...,
        description="Full audit provenance for the LASA detection run",
    )
    error_message: Optional[str] = Field(
        None,
        description="Error or unavailability details if status != 'completed'",
    )

    @model_validator(mode="before")
    @classmethod
    def sync_conflicts_and_status(cls, data: Any) -> Any:
        if isinstance(data, dict):
            status = data.get("status", "completed")
            cd = data.get("conflict_detected")
            hac = data.get("has_any_lasa_conflict")

            if status != "completed":
                # When failed or unavailable, conflict_detected must be None
                data["conflict_detected"] = None
                data["has_any_lasa_conflict"] = None
            else:
                # Sync cd and hac when completed
                resolved = cd if cd is not None else (hac if hac is not None else False)
                data["conflict_detected"] = resolved
                data["has_any_lasa_conflict"] = resolved
        return data
