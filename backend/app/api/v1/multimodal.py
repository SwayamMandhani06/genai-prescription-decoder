"""
Phase 6: Multimodal Vision-Language Extraction API Routes
Endpoints:
- POST /api/v1/multimodal/extract: Primary Vision-Language prescription extraction
- GET  /api/v1/multimodal/config: Multimodal model configuration and status audit
"""

import os
import uuid
from typing import Optional, Dict, Any

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException

from ...config import Settings, get_settings
from ...multimodal import (
    MultimodalExtractionService,
    PrescriptionExtractionResult,
    MultimodalConfig,
    MockMultimodalModelAdapter,
    GeminiMultimodalAdapter,
)
from ...schemas.error import ErrorCode, ErrorDetail, ErrorResponse
from ...services.storage import StorageService, FileValidationError
from ...services.pipeline_interface import PipelineProcessingError
from ...preprocessing import ImagePreprocessingService, ImageValidationError

router = APIRouter(prefix="/multimodal", tags=["Multimodal Vision Extraction"])

_storage_service = StorageService()
_preprocessing_service = ImagePreprocessingService()


def get_multimodal_service(settings: Settings = Depends(get_settings)) -> MultimodalExtractionService:
    """Dependency injector providing configured MultimodalExtractionService."""
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if gemini_key and len(gemini_key.strip()) > 5:
        cfg = MultimodalConfig(provider="gemini", configuration_status="implemented")
        adapter = GeminiMultimodalAdapter(config=cfg)
    else:
        cfg = MultimodalConfig(provider="mock", configuration_status="mock")
        adapter = MockMultimodalModelAdapter()
    return MultimodalExtractionService(adapter=adapter, config=cfg)


@router.get(
    "/config",
    summary="Get Multimodal Model Configuration and Audit Hash",
    description="Returns versioned model parameters, prompt version, and cryptographic SHA-256 config hash.",
)
async def get_config(
    service: MultimodalExtractionService = Depends(get_multimodal_service),
) -> Dict[str, Any]:
    cfg = service.config
    return {
        "config_version": cfg.config_version,
        "provider": cfg.provider,
        "model_id": cfg.model_id,
        "model_version": cfg.model_version,
        "temperature": cfg.temperature,
        "max_tokens": cfg.max_tokens,
        "timeout_seconds": cfg.timeout_seconds,
        "structured_output_mode": cfg.structured_output_mode,
        "prompt_version": cfg.prompt_version,
        "configuration_status": cfg.configuration_status,
        "is_adapter_available": service.adapter.is_available(),
        "config_hash_sha256": cfg.compute_config_hash(),
    }


@router.post(
    "/extract",
    response_model=PrescriptionExtractionResult,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid Request or Empty File"},
        413: {"model": ErrorResponse, "description": "Uploaded File Exceeds Allowed Size"},
        415: {"model": ErrorResponse, "description": "Unsupported File Type"},
        422: {"model": ErrorResponse, "description": "Pre-flight Quality Insufficient"},
        500: {"model": ErrorResponse, "description": "Multimodal Parsing or Inference Failure"},
        503: {"model": ErrorResponse, "description": "Multimodal Vision Model Unavailable"},
    },
    summary="Extract Prescription via Multimodal Vision Model",
    description="Ingests original prescription image as primary visual evidence and extracts structured posology.",
)
async def extract_prescription(
    file: UploadFile = File(..., description="Prescription image file (JPEG, PNG, WebP, TIFF)"),
    scenario: Optional[str] = Form(None, description="Optional deterministic test scenario override"),
    service: MultimodalExtractionService = Depends(get_multimodal_service),
) -> PrescriptionExtractionResult:
    # 1. Read image bytes
    try:
        content = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to read uploaded file stream: {str(exc)}",
        )

    if not content or len(content) < 10:
        err = ErrorResponse(
            error=ErrorDetail(
                code=ErrorCode.INVALID_REQUEST,
                message="Uploaded file payload is empty or unreadable.",
                stage="upload_validation",
                retryable=False,
            )
        )
        raise HTTPException(status_code=400, detail=err.model_dump())

    # 2. Store original prescription image
    filename = file.filename or "prescription.png"
    prescription_id = f"RX-{uuid.uuid4().hex[:8].upper()}"

    try:
        _storage_service.validate_file_metadata(
            filename=filename,
            content_type=file.content_type,
            size=len(content),
        )
        _, public_image_url = _storage_service.save_prescription_image(
            file_bytes=content,
            original_filename=filename,
        )
    except FileValidationError as fve:
        err = ErrorResponse(
            error=ErrorDetail(
                code=fve.code,
                message=fve.message,
                stage="file_storage",
                retryable=False,
            )
        )
        raise HTTPException(status_code=fve.status_code, detail=err.model_dump())

    # 3. Preprocess and assess quality
    derived_url: Optional[str] = None
    derived_bytes: Optional[bytes] = None
    try:
        res, manifest, derived_url = _preprocessing_service.process_and_store(
            image_bytes=content,
            filename=filename,
            prescription_id=prescription_id,
            reject_insufficient_quality=True,
        )
        if res.primary_processed_image:
            import io
            buf = io.BytesIO()
            res.primary_processed_image.save(buf, format="PNG")
            derived_bytes = buf.getvalue()
    except ImageValidationError as ive:
        err = ErrorResponse(
            error=ErrorDetail(
                code=ive.code,
                message=ive.message,
                stage=ive.stage,
                retryable=ive.retryable,
                details=ive.details,
            ),
            prescription_id=prescription_id,
            original_image_url=public_image_url,
        )
        raise HTTPException(status_code=ive.status_code, detail=err.model_dump())

    # 4. Multimodal Vision-Language Extraction
    try:
        result = await service.extract_prescription(
            image_bytes=content,
            prescription_id=prescription_id,
            original_image_url=public_image_url,
            mime_type=file.content_type or "image/jpeg",
            preprocessed_bytes=derived_bytes,
            preprocessed_image_url=derived_url,
            scenario=scenario,
        )
        return result
    except PipelineProcessingError as ppe:
        err = ErrorResponse(
            error=ErrorDetail(
                code=ppe.code,
                message=ppe.message,
                stage=ppe.stage,
                retryable=ppe.retryable,
                details=ppe.details,
            ),
            prescription_id=prescription_id,
            original_image_url=public_image_url,
        )
        raise HTTPException(status_code=ppe.status_code, detail=err.model_dump())

