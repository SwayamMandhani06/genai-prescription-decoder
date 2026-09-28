"""
FastAPI Routes for Phase 10: LASA (Look-Alike / Sound-Alike) Detection.
Endpoints:
- GET  /api/v1/lasa/config: Active LASA detection configuration
- POST /api/v1/lasa/screen: Screen a single medicine name for LASA conflicts
- POST /api/v1/lasa/detect: Detect LASA conflicts for a prescription (multiple medicines)
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ai.lasa.service import get_lasa_detection_service
from ai.lasa.config import TALL_MAN_PAIRS

router = APIRouter(prefix="/lasa", tags=["LASA Detection (Phase 10)"])


class ScreenMedicineRequest(BaseModel):
    candidate_name: str = Field(..., description="Extracted medicine name to screen for LASA conflicts")


class DetectPrescriptionRequest(BaseModel):
    prescription_id: str = Field(..., description="Prescription tracking identifier")
    medicine_names: List[str] = Field(..., min_length=1, description="List of extracted medicine names")


@router.get("/config")
async def get_lasa_configuration() -> Dict[str, Any]:
    """Returns the active LASA detection configuration and Tall Man pair count."""
    service = get_lasa_detection_service()
    config = service.config
    return {
        "status": "active",
        "policy_version": config.policy_version,
        "config_hash": config.config_hash(),
        "orthographic_threshold": config.orthographic_threshold,
        "phonetic_threshold": config.phonetic_threshold,
        "combined_threshold": config.combined_threshold,
        "orthographic_weight": config.orthographic_weight,
        "phonetic_weight": config.phonetic_weight,
        "high_risk_threshold": config.high_risk_threshold,
        "medium_risk_threshold": config.medium_risk_threshold,
        "known_pair_risk_override": config.known_pair_risk_override,
        "max_confusable_candidates": config.max_confusable_candidates,
        "known_pairs_count": len(TALL_MAN_PAIRS),
        "ismp_provenance": config.ismp_provenance,
    }


@router.post("/screen")
async def screen_single_medicine(request: ScreenMedicineRequest) -> Dict[str, Any]:
    """
    Screens a single medicine name for LASA (Look-Alike / Sound-Alike) conflicts
    against the authoritative reference pool and known ISMP pairs.
    """
    if not request.candidate_name or not request.candidate_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="candidate_name must not be empty",
        )

    service = get_lasa_detection_service()
    result = service.screen_single_medicine(
        candidate_name=request.candidate_name.strip(),
    )
    return {
        "status": "success",
        "result": result.model_dump(),
    }


@router.post("/detect")
async def detect_prescription_lasa(request: DetectPrescriptionRequest) -> Dict[str, Any]:
    """
    Runs full LASA detection for all medicines in a prescription.
    Returns prescription-level aggregation with per-medicine breakdowns.
    """
    cleaned_names = [n.strip() for n in request.medicine_names if n.strip()]
    if not cleaned_names:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="medicine_names must contain at least one non-empty medicine name",
        )

    service = get_lasa_detection_service()
    result = service.detect_prescription(
        prescription_id=request.prescription_id,
        medicine_names=cleaned_names,
    )
    return {
        "status": "success",
        "result": result.model_dump(),
    }
