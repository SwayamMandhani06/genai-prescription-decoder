"""
Prescription Processing API Routes
Implements endpoints:
- POST /api/v1/prescriptions/analyze
- GET  /api/v1/prescriptions/{prescription_id}
"""

from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query
from ...config import Settings, get_settings
from ...schemas.prescription import PrescriptionAnalyzeResponse
from ...schemas.error import ErrorCode, ErrorDetail, ErrorResponse
from ...services.storage import StorageService, FileValidationError
from ...services.pipeline_interface import (
    IPrescriptionPipeline,
    PipelineOptions,
    PipelineProcessingError,
)
from ...services.mock_pipeline import MockPrescriptionPipeline
from ...fixtures.mock_fixtures import (
    get_confident_fixture,
    get_uncertain_fixture,
    get_lasa_fixture,
    get_abstained_fixture,
)

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])

# Service dependency singletons
_storage_service = StorageService()
_mock_pipeline = MockPrescriptionPipeline()


def get_pipeline(settings: Settings = Depends(get_settings)) -> IPrescriptionPipeline:
    """Dependency injector returning the active processing pipeline."""
    # In Phase 2, the deterministic mock pipeline is active
    return _mock_pipeline


@router.post(
    "/analyze",
    response_model=PrescriptionAnalyzeResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid Request or Malformed Input"},
        413: {"model": ErrorResponse, "description": "Uploaded File Exceeds Allowed Size"},
        415: {"model": ErrorResponse, "description": "Unsupported Media File Type"},
        422: {"model": ErrorResponse, "description": "Diagnostic Pre-flight Validation Failure"},
        500: {"model": ErrorResponse, "description": "Internal Inference Processing Error"},
        503: {"model": ErrorResponse, "description": "Inference Worker Service Unavailable"},
        504: {"model": ErrorResponse, "description": "Upstream Drug Formulary Gateway Timeout"},
    },
    summary="Analyze Handwritten Prescription Document",
    description="Ingests an uploaded prescription image or sample ID, runs preprocessing and posology extraction, and returns evidence-grounded findings.",
)
async def analyze_prescription(
    file: Optional[UploadFile] = File(None, description="Handwritten prescription image file (JPEG, PNG, WebP, TIFF)"),
    sample_id: Optional[str] = Form(None, description="Pre-loaded academic evaluation sample ID (e.g. 'rx-sample-1')"),
    confidence_threshold: Optional[float] = Form(None, ge=0.0, le=1.0, description="Minimum confidence cutoff [0.0 - 1.0]"),
    enable_lasa_detection: Optional[bool] = Form(True, description="Enable Look-Alike Sound-Alike orthographic/phonetic screening"),
    target_language: Optional[str] = Form("en", description="Target regional language ('en', 'hi', 'mr') for patient explanation"),
    mock_scenario: Optional[str] = Form(None, description="Evaluation scenario override: confident, uncertain, lasa_warning, abstained, validation_error, server_error, timeout"),
    pipeline: IPrescriptionPipeline = Depends(get_pipeline),
) -> PrescriptionAnalyzeResponse:
    # 1. Validate that at least one input source is supplied
    if not file and not sample_id:
        raise HTTPException(
            status_code=400,
            detail="Either a prescription image 'file' or a curated 'sample_id' must be provided.",
        )

    file_bytes: Optional[bytes] = None
    filename: Optional[str] = None
    public_image_url: str = "/uploads/samples/sample-standard.svg"

    # 2. Process physical file upload if provided
    if file:
        filename = file.filename or "prescription.png"
        try:
            file_bytes = await file.read()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Unable to read incoming file stream: {str(e)}",
            )

        # Pre-flight validation (File size & MIME type)
        try:
            _storage_service.validate_file_metadata(
                filename=filename,
                content_type=file.content_type,
                size=len(file_bytes),
            )
        except FileValidationError as fve:
            raise HTTPException(
                status_code=fve.status_code,
                detail=fve.message,
            )

        # Store original image file (preserves original statutory reference)
        _, public_image_url = _storage_service.save_prescription_image(
            file_bytes=file_bytes,
            original_filename=filename,
        )
    elif sample_id:
        # Curated sample selection
        public_image_url = f"/uploads/samples/{sample_id}.svg"

    # 3. Assemble pipeline execution options
    options = PipelineOptions(
        confidence_threshold=confidence_threshold,
        enable_lasa_detection=bool(enable_lasa_detection),
        target_language=target_language or "en",
        mock_scenario=mock_scenario,
        sample_id=sample_id,
    )

    # 4. Execute the pipeline
    try:
        response = await pipeline.process_prescription(
            image_bytes=file_bytes,
            filename=filename,
            public_image_url=public_image_url,
            options=options,
        )
        return response
    except PipelineProcessingError as ppe:
        # Domain errors convert to uniform ErrorResponse
        raise ppe


@router.get(
    "/{prescription_id}",
    response_model=PrescriptionAnalyzeResponse,
    summary="Get Analyzed Prescription Record",
    description="Retrieves a previously processed prescription record or curated demo record by accession ID.",
)
async def get_prescription_by_id(
    prescription_id: str,
) -> PrescriptionAnalyzeResponse:
    norm_id = prescription_id.strip().upper()

    if norm_id in ("DEMO-RX-01", "RX-SAMPLE-1"):
        return get_confident_fixture(prescription_id=norm_id)
    elif norm_id in ("DEMO-RX-02", "RX-SAMPLE-2-UNCERTAIN"):
        return get_uncertain_fixture(prescription_id=norm_id)
    elif norm_id in ("DEMO-RX-04", "RX-SAMPLE-2", "DEMO-RX-LASA"):
        return get_lasa_fixture(prescription_id=norm_id)
    elif norm_id in ("DEMO-RX-05", "RX-SAMPLE-3", "DEMO-RX-ABSTAIN"):
        return get_abstained_fixture(prescription_id=norm_id)

    raise HTTPException(
        status_code=404,
        detail=f"Prescription with accession ID '{prescription_id}' was not found.",
    )
