"""
API Endpoints for Phase 7 RAG Medicine Validation.
Implements POST /api/v1/validation/medicine and associated routes according to PLAN.md Section 16 & 19.
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status

from backend.app.schemas.validation import (
    MedicineValidationRequest,
    MedicineValidationResponse,
    MedicineBatchValidationRequest,
    MedicineBatchValidationResponse,
)
from backend.app.schemas.error import ErrorCode, ErrorDetail, ErrorResponse
from ai.rag import get_medicine_validation_service, MedicineValidationService

logger = logging.getLogger("aura_rx.api.validation")

router = APIRouter(prefix="/validation", tags=["Phase 7 - RAG Medicine Validation"])


@router.post(
    "/medicine",
    response_model=MedicineValidationResponse,
    summary="Validate visually extracted medicine candidate against authoritative reference databases",
    description=(
        "Compares a candidate medicine name against CDSCO approved drug formulations and NLM RxNorm nomenclature. "
        "Returns controlled validation status ('validated', 'uncertain', 'not_validated'), retrieved top-k "
        "formulations, and full audit provenance without modifying observed posology or dosage."
    ),
)
async def validate_medicine(request: MedicineValidationRequest) -> MedicineValidationResponse:
    try:
        service = get_medicine_validation_service()
        result = service.validate_candidate(
            candidate_name=request.candidate_name,
            observed_dosage=request.observed_dosage,
            top_k=request.top_k or 5,
        )
        return MedicineValidationResponse(
            status="success",
            prescription_id=request.prescription_id,
            validation_result=result,
            ui_evidence=result.to_ui_validation_evidence(),
        )
    except Exception as e:
        logger.error("Medicine validation failed unexpectedly: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": ErrorCode.VALIDATION_FAILED.value,
                "message": f"Medicine validation service encountered an unexpected error: {str(e)}",
                "details": {"candidate_name": request.candidate_name},
            }
        )


@router.post(
    "/medicine/batch",
    response_model=MedicineBatchValidationResponse,
    summary="Batch validate multiple extracted medicine candidates",
    description="Validates an array of extracted medicine items, returning structured decisions for each item.",
)
async def validate_medicine_batch(request: MedicineBatchValidationRequest) -> MedicineBatchValidationResponse:
    try:
        service = get_medicine_validation_service()
        responses: List[MedicineValidationResponse] = []
        for item in request.items:
            result = service.validate_candidate(
                candidate_name=item.candidate_name,
                observed_dosage=item.observed_dosage,
                top_k=item.top_k or 5,
            )
            responses.append(
                MedicineValidationResponse(
                    status="success",
                    prescription_id=item.prescription_id,
                    validation_result=result,
                    ui_evidence=result.to_ui_validation_evidence(),
                )
            )
        return MedicineBatchValidationResponse(
            status="success",
            total_processed=len(responses),
            results=responses,
        )
    except Exception as e:
        logger.error("Batch medicine validation failed: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": ErrorCode.VALIDATION_FAILED.value,
                "message": f"Batch medicine validation failed: {str(e)}",
            }
        )


@router.get(
    "/status",
    summary="Get RAG reference database index and provenance status",
    description="Reports the operational status, loaded reference sources (CDSCO, RxNorm), index sizes, and config hash.",
)
async def get_validation_service_status() -> Dict[str, Any]:
    service = get_medicine_validation_service()
    return service.get_service_status()
