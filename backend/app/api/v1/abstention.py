"""
FastAPI Routes for Phase 9: Uncertainty-Aware Abstention and Human Verification.
Endpoints:
- GET  /api/v1/abstention/config: Active policy configuration, thresholds, and hash
- POST /api/v1/abstention/evaluate: Evaluates abstention decision for a posology field
- GET  /api/v1/abstention/fixtures: Lists all 15 deterministic Phase 9 test fixtures
- GET  /api/v1/abstention/fixtures/{fixture_id}: Retrieves a specific test fixture
- GET  /api/v1/verification/{prescription_id}: Retrieves human verification state and audit trail
- POST /api/v1/verification/{prescription_id}/fields/{field_id}/confirm: Submits confirmation
- POST /api/v1/verification/{prescription_id}/fields/{field_id}/correct: Submits correction
- POST /api/v1/verification/{prescription_id}/fields/{field_id}/unreadable: Submits unreadable mark
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.app.schemas.error import ErrorCode, ErrorDetail, ErrorResponse
from backend.app.multimodal.schemas import ExtractedField
from ai.rag.schemas import MedicineValidationResult, RetrievalCandidate, SourceProvenance
from ai.confidence.schemas import (
    FieldConfidenceAssessment,
    RawConfidenceSignal,
    CalibratedConfidence,
)
from ai.abstention.service import get_abstention_service
from ai.abstention.schemas import (
    FieldAbstentionDecision,
    HumanVerificationRecord,
    PrescriptionVerificationState,
)
from backend.app.fixtures.abstention_fixtures import (
    list_abstention_fixtures,
    get_abstention_fixture,
)

abstention_router = APIRouter(prefix="/abstention", tags=["Abstention Policy (Phase 9)"])
verification_router = APIRouter(prefix="/verification", tags=["Human Verification Workflow (Phase 9)"])


# ==============================================================================
# Request Models
# ==============================================================================

class EvaluateFieldAbstentionRequest(BaseModel):
    field_name: str = Field(..., description="Posology field key (e.g. 'medicine_name', 'dosage')")
    value: Optional[str] = Field(None, description="Extracted text from visual prescription")
    status: str = Field("confident", description="Extraction status: 'confident', 'uncertain', 'flagged'")
    presence: str = Field("present", description="Field presence: 'present' or 'absent'")
    extraction_state: str = Field("extracted", description="Extraction state: 'extracted', 'ambiguous', 'missing'")
    raw_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Raw model signal")
    calibrated_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Calibrated probability")
    calibration_status: str = Field("insufficient_data", description="Status of probability calibration")
    calibration_method: Optional[str] = Field(None, description="Applied calibration algorithm")
    conflict_detected: bool = Field(False, description="Whether visual/retrieval conflict was detected")
    conflict_description: Optional[str] = Field(None, description="Details of detected conflict")
    candidates: List[str] = Field(default_factory=list, description="Competing visual candidate interpretations")
    uncertainty_reason: Optional[str] = Field(None, description="Observational reason for ambiguity")
    observed_dosage: Optional[str] = Field(None, description="Observed dosage string (dosage invariant)")
    reference_strength: Optional[str] = Field(None, description="Strength from reference formulary")
    formulation_consistency: str = Field("consistent", description="Formulation consistency status")


class ConfirmFieldRequest(BaseModel):
    original_value: Optional[str] = Field(None, description="Original unedited model value")
    reason: Optional[str] = Field(None, description="Clinical verification rationale")


class CorrectFieldRequest(BaseModel):
    corrected_value: str = Field(..., min_length=1, description="Transcribed correction from visual script")
    original_value: Optional[str] = Field(None, description="Original unedited model value")
    reason: Optional[str] = Field(None, description="Clinical reason for correction")


class MarkUnreadableRequest(BaseModel):
    original_value: Optional[str] = Field(None, description="Original unedited model value")
    reason: Optional[str] = Field(None, description="Reason for declaring unreadable")


# ==============================================================================
# Abstention Endpoints
# ==============================================================================

@abstention_router.get("/config")
async def get_abstention_policy_config() -> Dict[str, Any]:
    """Returns the active versioned abstention policy configuration and fingerprint."""
    service = get_abstention_service()
    return {
        "status": "success",
        "policy_version": service.config.policy_version,
        "config_hash": service.config.get_config_hash(),
        "min_calibrated_confidence": service.config.min_calibrated_confidence,
        "require_calibration_for_acceptance": service.config.require_calibration_for_acceptance,
        "abstain_on_extraction_uncertain": service.config.abstain_on_extraction_uncertain,
        "abstain_on_field_missing": service.config.abstain_on_field_missing,
        "abstain_on_conflict": service.config.abstain_on_conflict,
        "abstain_on_multiple_candidates": service.config.abstain_on_multiple_candidates,
        "dosage_strict_mode": service.config.dosage_strict_mode,
        "allow_uncalibrated_acceptance": service.config.allow_uncalibrated_acceptance,
        "min_raw_confidence_fallback": service.config.min_raw_confidence_fallback,
        "description": service.config.description,
    }


@abstention_router.post("/evaluate", response_model=FieldAbstentionDecision)
async def evaluate_field_decision(payload: EvaluateFieldAbstentionRequest):
    """
    Evaluates whether an individual posology field should be accepted or abstained.
    """
    service = get_abstention_service()

    ext_field = ExtractedField(
        value=payload.value,
        status=payload.status,  # type: ignore[arg-type]
        presence=payload.presence,  # type: ignore[arg-type]
        extraction_state=payload.extraction_state,  # type: ignore[arg-type]
        confidence=payload.raw_confidence,
        candidates=payload.candidates,
        uncertainty_reason=payload.uncertainty_reason,
    )

    conf_assessment = FieldConfidenceAssessment(
        field_name=payload.field_name,
        observed_value=payload.value,
        raw_signal=RawConfidenceSignal(
            source="multimodal_extraction",
            raw_value=payload.raw_confidence,
            signal_type="model_visual_stroke_confidence",
        ),
        calibrated=CalibratedConfidence(
            value=payload.calibrated_confidence,
            calibration_method=payload.calibration_method,  # type: ignore[arg-type]
            calibration_status=payload.calibration_status,  # type: ignore[arg-type]
        ),
        status="uncertain" if payload.status == "uncertain" else ("flagged" if payload.status == "flagged" else "confident"),
        conflict_detected=payload.conflict_detected,
        conflict_description=payload.conflict_description,
    )

    val_res: Optional[MedicineValidationResult] = None
    if payload.observed_dosage or payload.reference_strength or payload.formulation_consistency != "consistent":
        val_res = MedicineValidationResult(
            input_candidate=payload.value or "",
            normalized_candidate=(payload.value or "").lower(),
            validation_status="uncertain" if payload.formulation_consistency == "mismatch" else "validated",
            medicine_identity_status="validated",
            evidence="Validation formulation check",
            observed_dosage=payload.observed_dosage,
            reference_strength=payload.reference_strength,
            formulation_consistency=payload.formulation_consistency,  # type: ignore[arg-type]
            dosage_observation_preserved=True,
            provenance={  # type: ignore[arg-type]
                "retrieval_method": "exact_normalized_name",
                "query_raw": payload.value or "",
                "query_normalized": (payload.value or "").lower(),
                "normalization_version": "v1.0",
                "index_version": "v1.0",
                "config_hash": "mock",
                "matched_count": 1,
                "timestamp": "2026-09-27T00:00:00Z",
                "validation_rule": "FORMULATION_CHECK",
                "source_authorities": ["cdsco"],
            },
        )

    from ai.abstention.policy import evaluate_field_abstention
    return evaluate_field_abstention(
        field_name=payload.field_name,
        extracted_field=ext_field,
        confidence_assessment=conf_assessment,
        validation_result=val_res,
        config=service.config,
    )


@abstention_router.get("/fixtures")
async def get_fixtures() -> List[Dict[str, Any]]:
    """Returns all 15 deterministic Phase 9 evaluation fixtures."""
    return list_abstention_fixtures()


@abstention_router.get("/fixtures/{fixture_id}")
async def get_fixture_by_id(fixture_id: str) -> Dict[str, Any]:
    """Retrieves a specific Phase 9 fixture by ID."""
    try:
        return get_abstention_fixture(fixture_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phase 9 fixture '{fixture_id}' not found.",
        )


# ==============================================================================
# Human Verification Endpoints
# ==============================================================================

@verification_router.get("/{prescription_id}", response_model=PrescriptionVerificationState)
async def get_prescription_verification_state(prescription_id: str):
    """
    Retrieves the current human verification state and complete audit trail for a prescription.
    """
    if not prescription_id or prescription_id.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="prescription_id cannot be empty.",
        )
    service = get_abstention_service()
    state = service.get_verification_state(prescription_id)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification state for prescription '{prescription_id}' not found.",
        )
    return state


@verification_router.post(
    "/{prescription_id}/fields/{field_id}/confirm",
    response_model=HumanVerificationRecord,
)
async def confirm_prescription_field(
    prescription_id: str,
    field_id: str,
    payload: ConfirmFieldRequest,
):
    """
    Confirms an extracted posology field against the visual prescription image.
    """
    if not prescription_id or not field_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="prescription_id and field_id are required.",
        )
    service = get_abstention_service()
    record = service.confirm_field(
        prescription_id=prescription_id,
        field_id=field_id,
        original_value=payload.original_value,
        reason=payload.reason,
    )
    return record


@verification_router.post(
    "/{prescription_id}/fields/{field_id}/correct",
    response_model=HumanVerificationRecord,
)
async def correct_prescription_field(
    prescription_id: str,
    field_id: str,
    payload: CorrectFieldRequest,
):
    """
    Records a human correction for an ambiguous or misread field, preserving original extraction.
    """
    if not prescription_id or not field_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="prescription_id and field_id are required.",
        )
    if not payload.corrected_value or payload.corrected_value.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="corrected_value cannot be empty or whitespace.",
        )

    service = get_abstention_service()
    try:
        record = service.correct_field(
            prescription_id=prescription_id,
            field_id=field_id,
            corrected_value=payload.corrected_value,
            original_value=payload.original_value,
            reason=payload.reason,
        )
        return record
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@verification_router.post(
    "/{prescription_id}/fields/{field_id}/unreadable",
    response_model=HumanVerificationRecord,
)
async def mark_prescription_field_unreadable(
    prescription_id: str,
    field_id: str,
    payload: MarkUnreadableRequest,
):
    """
    Marks a field as optically or clinically unreadable. Does not force guessing.
    """
    if not prescription_id or not field_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="prescription_id and field_id are required.",
        )
    service = get_abstention_service()
    record = service.mark_field_unreadable(
        prescription_id=prescription_id,
        field_id=field_id,
        original_value=payload.original_value,
        reason=payload.reason,
    )
    return record
