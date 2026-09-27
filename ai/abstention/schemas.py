"""
Phase 9: Uncertainty-Aware Abstention and Human Verification Schemas.
Typed contracts for:
- Field-level and prescription-level abstention decisions
- Configurable decision metadata and machine-readable reason codes
- Human verification actions (confirm, correct, mark_unreadable)
- Immutable audit trail records preserving original extractions
"""

from typing import Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field

DecisionState = Literal["accepted", "abstained"]
PrescriptionDecisionState = Literal["ACCEPTED", "REQUIRES_HUMAN_VERIFICATION", "READY_FOR_REVIEW"]
VerificationStatus = Literal["pending", "confirmed", "corrected", "unreadable"]
VerifierActionType = Literal["confirm", "correct", "mark_unreadable"]


class FieldConfidenceMetadata(BaseModel):
    """
    Confidence context accompanying an abstention decision.
    Strictly separates raw score from calibrated probability.
    """
    raw_value: Optional[float] = Field(
        None,
        description="Uncalibrated model/retrieval signal score [0.0 - 1.0]"
    )
    calibrated_value: Optional[float] = Field(
        None,
        description="Calibrated probability of correctness [0.0 - 1.0]. None if uncalibrated or data insufficient."
    )
    calibration_status: str = Field(
        ...,
        description="Status: 'calibrated', 'uncalibrated', 'insufficient_data', 'not_available'"
    )
    calibration_method: Optional[str] = Field(
        None,
        description="Method used for calibration, if applicable"
    )


class FieldAbstentionDecision(BaseModel):
    """
    Explicit decision for an individual posology field.
    Provides machine-readable reasons and human-readable guidance.
    """
    field_name: str = Field(..., description="Posology field identifier (e.g. 'medicine_name', 'dosage', 'frequency')")
    field_label: str = Field(..., description="Human-readable field title for display")
    original_value: Optional[str] = Field(None, description="Extracted text from visual prescription (immutable)")
    decision: DecisionState = Field(..., description="'accepted' if evidence is sufficient; 'abstained' if uncertain")
    requires_human_verification: bool = Field(..., description="True if clinician/pharmacist verification is mandated")
    reason_codes: List[str] = Field(default_factory=list, description="Standardized machine-readable reason codes")
    reasons_detail: List[str] = Field(default_factory=list, description="Human-readable clinical rationale for decision")
    confidence: FieldConfidenceMetadata = Field(..., description="Underlying confidence state")
    conflicts: List[str] = Field(default_factory=list, description="Detected evidentiary conflicts")
    observed_dosage_preserved: Optional[bool] = Field(
        None,
        description="Explicitly True for dosage fields to guarantee observed value was not overwritten"
    )
    reference_evidence: Optional[Dict[str, Any]] = Field(
        None,
        description="Authoritative formulary reference evidence, if matched"
    )
    selective_metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Selective-prediction telemetry reserved for Phase 12 empirical risk-coverage evaluation"
    )


class MedicineAbstentionDecision(BaseModel):
    """
    Line-item level aggregation of field abstention decisions for a single medication.
    """
    item_index: int = Field(..., ge=1, description="1-based index of medication line item")
    medicine_name: str = Field(..., description="Candidate or extracted medicine name")
    decision: DecisionState = Field(..., description="Line-item decision ('accepted' or 'abstained')")
    requires_human_verification: bool = Field(..., description="True if any field in this line item requires verification")
    fields: Dict[str, FieldAbstentionDecision] = Field(..., description="Field-level decisions for this medicine")
    abstained_fields_count: int = Field(0, description="Count of abstained fields in this medication")
    total_fields_count: int = Field(0, description="Total posology fields evaluated")


class PrescriptionAbstentionDecision(BaseModel):
    """
    Document-level abstention decision consolidating all field-level and medicine-level assessments.
    """
    prescription_id: str = Field(..., description="Statutory unique prescription tracking identifier")
    policy_version: str = Field(..., description="Version of the active abstention policy (e.g. 'abstention_policy_v1')")
    prescription_decision: PrescriptionDecisionState = Field(
        ...,
        description="'ACCEPTED' (all fields pass policy), 'REQUIRES_HUMAN_VERIFICATION', or 'READY_FOR_REVIEW'"
    )
    requires_human_verification: bool = Field(
        ...,
        description="True if one or more fields trigger an abstention condition"
    )
    fields: Dict[str, FieldAbstentionDecision] = Field(
        default_factory=dict,
        description="Primary field-level decisions (conforming to PLAN.md Section 6 field keys)"
    )
    medicines: List[MedicineAbstentionDecision] = Field(
        default_factory=list,
        description="Medication-level decisions for multi-line prescriptions"
    )
    fields_requiring_verification: List[str] = Field(
        default_factory=list,
        description="List of field identifiers requiring human action"
    )
    total_fields_evaluated: int = Field(0, description="Count of all posology fields evaluated")
    abstained_fields_count: int = Field(0, description="Count of fields that were abstained")
    abstention_rate: float = Field(0.0, ge=0.0, le=1.0, description="Fraction of evaluated fields abstained")
    summary: str = Field(..., description="High-level clinical summary of the abstention determination")
    original_image_url: Optional[str] = Field(None, description="Authoritative original image reference for verifier")
    config_hash: str = Field(..., description="SHA-256 fingerprint of the active abstention configuration")
    timestamp: str = Field(..., description="ISO 8601 evaluation timestamp")


# ==============================================================================
# Human Verification Workflow Schemas
# ==============================================================================

class HumanVerificationActionRequest(BaseModel):
    """
    Payload submitted by a human verifier for a specific field.
    """
    action: VerifierActionType = Field(
        ...,
        description="Action performed: 'confirm' (accept original), 'correct' (provide edited text), 'mark_unreadable'"
    )
    verified_value: Optional[str] = Field(
        None,
        description="Corrected text if action is 'correct'; unchanged text if 'confirm'; None if 'mark_unreadable'"
    )
    reason: Optional[str] = Field(
        None,
        description="Optional explanatory reason for the verification action"
    )
    verifier_notes: Optional[str] = Field(
        None,
        description="Optional clinical observations recorded by the human reviewer"
    )


class HumanVerificationRecord(BaseModel):
    """
    Immutable audit trail record capturing a verification action.
    Preserves original model extraction alongside verified determination.
    """
    verification_id: str = Field(..., description="Unique UUID for this verification event")
    prescription_id: str = Field(..., description="Prescription identifier")
    field_id: str = Field(..., description="Target field key (e.g. 'medicine_name', 'dosage')")
    original_value: Optional[str] = Field(None, description="Unmodified original value produced by AI pipeline")
    verified_value: Optional[str] = Field(None, description="Final human-verified text determination")
    verification_status: VerificationStatus = Field(
        ...,
        description="Current state: 'pending', 'confirmed', 'corrected', or 'unreadable'"
    )
    verifier_action: VerifierActionType = Field(
        ...,
        description="Action type executed: 'confirm', 'correct', or 'mark_unreadable'"
    )
    reason: Optional[str] = Field(None, description="Reason recorded for action")
    timestamp: str = Field(..., description="ISO 8601 audit timestamp")
    policy_version: str = Field(..., description="Active abstention policy version at time of verification")
    system_version: str = Field("1.0.0", description="AURA-Rx system version")


class PrescriptionVerificationState(BaseModel):
    """
    Aggregated human verification state for a prescription document.
    Maintains active records and complete historical audit trail.
    """
    prescription_id: str = Field(..., description="Prescription tracking identifier")
    original_image_url: str = Field(..., description="Preserved authoritative URL for the uploaded prescription image")
    overall_verification_status: Literal["pending", "in_progress", "completed"] = Field(
        "pending",
        description="Overall review state for the document"
    )
    records: Dict[str, HumanVerificationRecord] = Field(
        default_factory=dict,
        description="Current verification record per field_id"
    )
    audit_trail: List[HumanVerificationRecord] = Field(
        default_factory=list,
        description="Chronological append-only audit trail of all verification actions"
    )
    pending_fields: List[str] = Field(
        default_factory=list,
        description="List of fields still awaiting human verification"
    )
    verified_fields: List[str] = Field(
        default_factory=list,
        description="List of fields that have been confirmed, corrected, or marked unreadable"
    )
    updated_at: str = Field(..., description="ISO 8601 timestamp of last verification state modification")
