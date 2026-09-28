"""
FastAPI Routes for Phase 11: Multilingual Patient-Friendly Explanation.
Endpoints:
- GET  /api/v1/explanation/config: Active explanation configuration and version hash
- POST /api/v1/explanation/generate: Generate verified multilingual posology explanation
- GET  /api/v1/explanation/fixtures: Standard test and evaluation fixtures (Dev Only)
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ai.explanation.config import (
    CONFIG_HASH,
    EXPLANATION_PROVENANCE_METADATA,
    POLICY_VERSION,
    SUPPORTED_LANGUAGES,
    TEMPLATE_VERSION,
    TERMINOLOGY_VERSION,
)
from ai.explanation.fixtures import EXPLANATION_FIXTURES
from ai.explanation.schemas import (
    ExplanationEligibilityStatus,
    MultilingualPrescriptionExplanation,
)
from ai.explanation.service import get_explanation_service

router = APIRouter(prefix="/explanation", tags=["Multilingual Explanation (Phase 11)"])


class GenerateExplanationRequest(BaseModel):
    """
    Structured request contract for generating patient explanations.
    Must consume structured clinical fields only; does NOT accept arbitrary freeform text.
    """
    prescription_id: str = Field(..., description="Prescription tracking identifier")
    medicine_name: Optional[str] = Field(None, description="Extracted medicine name")
    dosage: Optional[str] = Field(None, description="Extracted dosage/strength (e.g. 500 mg)")
    frequency: Optional[str] = Field(None, description="Extracted frequency (e.g. twice daily, 1-0-1)")
    duration: Optional[str] = Field(None, description="Extracted duration (e.g. 5 days)")
    candidate_status: Optional[str] = Field("confident", description="Visual confidence status")
    validation_status: Optional[str] = Field("validated", description="RAG reference validation status")
    abstention_decision: Optional[str] = Field("accepted", description="Phase 9 abstention decision")
    requires_human_verification: bool = Field(False, description="Whether clinician review is mandated")
    has_lasa_conflict: bool = Field(False, description="Whether LASA similarity conflict was detected")
    confusable_counterpart: Optional[str] = Field(None, description="Confusing drug counterpart if LASA flagged")
    human_verification_status: Optional[str] = Field(None, description="unreadable | corrected | confirmed")
    human_verified_value: Optional[str] = Field(None, description="Corrected drug name if human corrected")
    is_service_healthy: bool = Field(True, description="Service operational state")


@router.get("/config")
async def get_explanation_configuration() -> Dict[str, Any]:
    """Returns the active explanation policy configuration, terminology version, and SHA-256 fingerprint."""
    return {
        "status": "active",
        "policy_version": POLICY_VERSION,
        "template_version": TEMPLATE_VERSION,
        "terminology_version": TERMINOLOGY_VERSION,
        "config_hash": CONFIG_HASH,
        "supported_languages": SUPPORTED_LANGUAGES,
        "provenance": EXPLANATION_PROVENANCE_METADATA,
    }


@router.post("/generate", response_model=MultilingualPrescriptionExplanation)
async def generate_explanation(request: GenerateExplanationRequest) -> MultilingualPrescriptionExplanation:
    """
    Generates verified, patient-friendly explanations in English, Hindi, and Marathi
    from structured prescription facts.
    """
    if not request.prescription_id or not request.prescription_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="prescription_id must not be empty",
        )

    service = get_explanation_service()
    result = service.generate_explanation(
        prescription_id=request.prescription_id.strip(),
        medicine_name=request.medicine_name.strip() if request.medicine_name else None,
        dosage=request.dosage.strip() if request.dosage else None,
        frequency=request.frequency.strip() if request.frequency else None,
        duration=request.duration.strip() if request.duration else None,
        candidate_status=request.candidate_status,
        validation_status=request.validation_status,
        abstention_decision=request.abstention_decision,
        requires_human_verification=request.requires_human_verification,
        has_lasa_conflict=request.has_lasa_conflict,
        confusable_counterpart=request.confusable_counterpart,
        human_verification_status=request.human_verification_status,
        human_verified_value=request.human_verified_value,
        is_service_healthy=request.is_service_healthy,
    )
    return result


@router.get("/fixtures")
async def get_mock_fixtures() -> Dict[str, Any]:
    """
    Returns deterministic development mock fixtures for testing.
    All returned items are clearly marked as development fixtures.
    """
    return {
        "notice": "DEVELOPMENT TEST FIXTURES ONLY: Not for clinical or diagnostic use.",
        "fixture_count": len(EXPLANATION_FIXTURES),
        "fixtures": EXPLANATION_FIXTURES,
    }
