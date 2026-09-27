"""
Phase 5: Research OCR Baseline API Endpoints
Provides dedicated routes for executing and comparing conventional OCR baseline.
Strictly isolated from production multimodal inference and clinical interpretation.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from ...ocr import (
    OCRBaselineConfig,
    OCRBaselineService,
    OCRRunResult,
    TesseractEngine,
)
from ...schemas.error import ErrorCode, ErrorDetail, ErrorResponse
from ...services.pipeline_interface import PipelineProcessingError
from ...services.storage import StorageService

router = APIRouter(prefix="/ocr", tags=["Research OCR Baseline"])

_ocr_service = OCRBaselineService()
_storage_service = StorageService()

SAMPLE_DIR = Path("data/samples")


def resolve_sample_image(sample_id: str) -> Path:
    """Resolves sample ID or alias to physical file in data/samples/."""
    clean_id = sample_id.strip().lower()
    mapping = {
        "sample-1": "sample_01_clear.png",
        "rx-sample-1": "sample_01_clear.png",
        "doc-rx-001": "sample_01_clear.png",
        "sample-2": "sample_02_cursive.png",
        "rx-sample-2": "sample_02_cursive.png",
        "doc-rx-002": "sample_02_cursive.png",
        "sample-3": "sample_03_blurred.png",
        "doc-rx-003": "sample_03_blurred.png",
        "sample-4": "sample_04_lowlight.png",
        "doc-rx-004": "sample_04_lowlight.png",
        "sample-5": "sample_05_abbreviations.png",
        "doc-rx-005": "sample_05_abbreviations.png",
        "sample-6": "sample_06_lasa_pair.png",
        "doc-rx-006": "sample_06_lasa_pair.png",
        "sample-7": "sample_07_ambiguous_abstain.png",
        "doc-rx-007": "sample_07_ambiguous_abstain.png",
    }

    filename = mapping.get(clean_id)
    if filename:
        p = SAMPLE_DIR / filename
        if p.is_file():
            return p

    # Fallback to direct name in directory
    direct = SAMPLE_DIR / sample_id
    if direct.is_file():
        return direct

    direct_png = SAMPLE_DIR / f"{sample_id}.png"
    if direct_png.is_file():
        return direct_png

    raise HTTPException(
        status_code=404,
        detail=f"Sample image '{sample_id}' not found in '{SAMPLE_DIR}'.",
    )


@router.get(
    "/baseline/engine",
    summary="Get OCR Baseline Engine Status",
    description="Returns runtime status, detected binary path, real version, and installed languages of the baseline engine.",
)
async def get_engine_status():
    engine = _ocr_service.engine
    is_avail = engine.is_available()
    binary_path = engine.get_binary_path()
    version = engine.get_version() if is_avail else None
    languages = engine.get_available_languages() if is_avail else []

    return {
        "engine": "tesseract",
        "available": is_avail,
        "binary_path": binary_path,
        "version": version,
        "languages": languages,
        "default_configuration": {
            "configuration_id": _ocr_service.ocr_config.configuration_id,
            "configuration_hash": _ocr_service.ocr_config.compute_config_hash(),
            "language": _ocr_service.ocr_config.language,
            "psm": _ocr_service.ocr_config.psm,
            "oem": _ocr_service.ocr_config.oem,
            "preprocessing_variant": _ocr_service.ocr_config.preprocessing_variant,
            "timeout_seconds": _ocr_service.ocr_config.timeout_seconds,
        },
    }


@router.post(
    "/baseline",
    response_model=OCRRunResult,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid Request"},
        413: {"model": ErrorResponse, "description": "File Too Large"},
        415: {"model": ErrorResponse, "description": "Unsupported File Type"},
        500: {"model": ErrorResponse, "description": "Processing Failed"},
        503: {"model": ErrorResponse, "description": "OCR Engine Unavailable"},
    },
    summary="Execute Conventional OCR Baseline",
    description="Runs the reproducible conventional OCR baseline on an uploaded prescription or sample image, returning immutable raw output and spatial tokens.",
)
async def run_baseline_ocr(
    file: Optional[UploadFile] = File(None, description="Prescription image file"),
    sample_id: Optional[str] = Form(None, description="Pre-loaded academic sample ID"),
    prescription_id: Optional[str] = Form(None, description="Accession ID if associated with existing document"),
    preprocessing_variant: Optional[str] = Form(
        "enhanced",
        description="Preprocessing variant ('enhanced', 'grayscale', 'thresholded', 'original', 'deskewed')",
    ),
    psm: Optional[int] = Form(6, description="Tesseract Page Segmentation Mode"),
) -> OCRRunResult:
    if not file and not sample_id:
        raise HTTPException(
            status_code=400,
            detail="Either a prescription image 'file' or a curated 'sample_id' must be provided.",
        )

    file_bytes: bytes
    filename: Optional[str] = None

    if file:
        filename = file.filename or "prescription.png"
        try:
            file_bytes = await file.read()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Unable to read incoming file stream: {str(e)}",
            )
        # Validate metadata
        _storage_service.validate_file_metadata(
            filename=filename,
            content_type=file.content_type,
            size=len(file_bytes),
        )
    else:
        sample_path = resolve_sample_image(sample_id)
        filename = sample_path.name
        with open(sample_path, "rb") as f:
            file_bytes = f.read()

    # Configure overrides if specified
    cfg = OCRBaselineConfig(
        psm=psm or 6,
        preprocessing_variant=preprocessing_variant or "enhanced",
    )

    try:
        result = _ocr_service.run_ocr(
            image_input=file_bytes,
            filename=filename,
            prescription_id=prescription_id,
            preprocessing_variant=preprocessing_variant,
            config_override=cfg,
        )
        return result
    except PipelineProcessingError:
        raise
    except Exception as e:
        raise PipelineProcessingError(
            code=ErrorCode.PROCESSING_FAILED,
            message=f"OCR baseline execution encountered an error: {str(e)}",
            stage="ocr_baseline_service",
            retryable=False,
        )


@router.post(
    "/baseline/compare",
    response_model=Dict[str, OCRRunResult],
    summary="Compare OCR Across Preprocessing Variants",
    description="Executes conventional OCR across all Phase 4 derived representations (original, grayscale, enhanced, deskewed, thresholded) for controlled comparison.",
)
async def compare_baseline_variants(
    file: Optional[UploadFile] = File(None, description="Prescription image file"),
    sample_id: Optional[str] = Form(None, description="Pre-loaded academic sample ID"),
    prescription_id: Optional[str] = Form(None, description="Accession ID if associated with existing document"),
) -> Dict[str, OCRRunResult]:
    if not file and not sample_id:
        raise HTTPException(
            status_code=400,
            detail="Either a prescription image 'file' or a curated 'sample_id' must be provided.",
        )

    file_bytes: bytes
    filename: Optional[str] = None

    if file:
        filename = file.filename or "prescription.png"
        file_bytes = await file.read()
        _storage_service.validate_file_metadata(
            filename=filename,
            content_type=file.content_type,
            size=len(file_bytes),
        )
    else:
        sample_path = resolve_sample_image(sample_id)
        filename = sample_path.name
        with open(sample_path, "rb") as f:
            file_bytes = f.read()

    try:
        results = _ocr_service.run_variant_comparison(
            image_bytes=file_bytes,
            filename=filename,
            prescription_id=prescription_id,
        )
        return results
    except PipelineProcessingError:
        raise
    except Exception as e:
        raise PipelineProcessingError(
            code=ErrorCode.PROCESSING_FAILED,
            message=f"Variant comparison failed: {str(e)}",
            stage="ocr_variant_comparison",
            retryable=False,
        )
