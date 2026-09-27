"""
Deterministic Mock Processing Pipeline
Implements IPrescriptionPipeline for Phase 2.
Produces deterministic, reproducible fixtures required for the frozen Phase 1 frontend.
Clearly identifies outputs as simulated mock predictions without fabricating real AI metrics.
"""

import uuid
from typing import Optional
from .pipeline_interface import IPrescriptionPipeline, PipelineOptions, PipelineProcessingError
from ..schemas.prescription import PrescriptionAnalyzeResponse
from ..schemas.error import ErrorCode
from ..fixtures.mock_fixtures import (
    get_confident_fixture,
    get_uncertain_fixture,
    get_lasa_fixture,
    get_abstained_fixture,
)


class MockPrescriptionPipeline(IPrescriptionPipeline):
    """
    Deterministic mock pipeline for Phase 2 API integration and verification.
    """

    async def process_prescription(
        self,
        image_bytes: Optional[bytes],
        filename: Optional[str],
        public_image_url: str,
        options: PipelineOptions,
    ) -> PrescriptionAnalyzeResponse:
        scenario = options.mock_scenario
        sample_id = options.sample_id
        prescription_id = f"RX-{uuid.uuid4().hex[:8].upper()}"

        # ------------------------------------------------------------------
        # 1. Fault Injection / Error Scenarios (PLAN.md Section 6 & 11)
        # ------------------------------------------------------------------
        if scenario in ("image_quality_insufficient", "low_quality", "insufficient_quality"):
            raise PipelineProcessingError(
                code=ErrorCode.IMAGE_QUALITY_INSUFFICIENT,
                message="Prescription image quality is insufficient for clinical interpretation (effective resolution below 150 DPI threshold or severe optical degradation).",
                stage="image_quality_assessment",
                status_code=422,
                retryable=True,
                details={
                    "minimum_dpi": 150,
                    "detected_dpi": 96,
                    "blur_score": 38.4,
                    "contrast_ratio": 1.4,
                    "recommendation": "Retake prescription photo with direct overhead lighting, high resolution, and avoid motion blur.",
                },
                prescription_id=prescription_id,
                original_image_url=public_image_url,
            )

        if scenario == "validation_error":
            raise PipelineProcessingError(
                code=ErrorCode.VALIDATION_FAILED,
                message="Prescription posology validation failed: conflicting dosage instructions or unrecognized formulation structure.",
                stage="posology_validation",
                status_code=422,
                retryable=True,
                details={
                    "field": "dosage",
                    "rule": "posology_coherence",
                    "extracted_raw": "q4h 1000mg tds",
                    "recommendation": "Physician clarification required for ambiguous dosage schedule.",
                },
                prescription_id=prescription_id,
                original_image_url=public_image_url,
            )

        if scenario in ("server_error", "processing_failed"):
            raise PipelineProcessingError(
                code=ErrorCode.PROCESSING_FAILED,
                message="Internal pipeline execution failure: Cross-attention decoder state collapsed on degraded ligature.",
                stage="multimodal_extraction",
                status_code=500,
                retryable=True,
                details={"worker_node": "mock-gpu-node-01", "error_type": "AttentionCollapse"},
                prescription_id=prescription_id,
                original_image_url=public_image_url,
            )

        if scenario == "model_unavailable":
            raise PipelineProcessingError(
                code=ErrorCode.MODEL_UNAVAILABLE,
                message="Prescription multimodal inference worker service is temporarily offline or unavailable (503 Service Unavailable).",
                stage="inference_dispatch",
                status_code=503,
                retryable=True,
                details={"service": "swin_multimodal_worker", "retry_after_seconds": 5},
                prescription_id=prescription_id,
                original_image_url=public_image_url,
            )

        if scenario == "timeout":
            raise PipelineProcessingError(
                code=ErrorCode.INTERNAL_ERROR,
                message="CDSCO Drug Database & RxNorm Formulary Gateway connection timed out after 15,000ms.",
                stage="evidence_retrieval",
                status_code=504,
                retryable=True,
                details={"timeout_ms": 15000, "target_endpoint": "https://cdsco.gov.in/api/v1/search"},
                prescription_id=prescription_id,
                original_image_url=public_image_url,
            )

        # ------------------------------------------------------------------
        # 2. Phase 4 Preprocessing & Quality Assessment Execution
        # ------------------------------------------------------------------
        from ..preprocessing import ImagePreprocessingService, ImageValidationError

        preprocessing_service = ImagePreprocessingService()
        processed_image_url: Optional[str] = None
        quality_report_dict: Optional[dict] = None
        preprocessing_manifest_dict: Optional[dict] = None

        if image_bytes and len(image_bytes) > 0 and image_bytes != b"dummy":
            try:
                res, manifest, derived_url = preprocessing_service.process_and_store(
                    image_bytes=image_bytes,
                    filename=filename,
                    prescription_id=prescription_id,
                    reject_insufficient_quality=True,
                )
                processed_image_url = derived_url
                quality_report_dict = res.quality_report.model_dump()
                preprocessing_manifest_dict = manifest.model_dump()
            except ImageValidationError as ive:
                raise PipelineProcessingError(
                    code=ive.code,
                    message=ive.message,
                    stage=ive.stage,
                    status_code=ive.status_code,
                    retryable=ive.retryable,
                    details=ive.details,
                    prescription_id=prescription_id,
                    original_image_url=public_image_url,
                )

        # ------------------------------------------------------------------
        # 3. Deterministic Scenario Matching (options.mock_scenario or sample_id)
        # ------------------------------------------------------------------
        if scenario == "uncertain":
            response = get_uncertain_fixture(prescription_id=prescription_id, image_url=public_image_url)
        elif scenario == "lasa_warning" or sample_id == "rx-sample-2":
            response = get_lasa_fixture(prescription_id=prescription_id, image_url=public_image_url)
        elif scenario in ("abstained", "flagged") or sample_id == "rx-sample-3":
            response = get_abstained_fixture(prescription_id=prescription_id, image_url=public_image_url)
        else:
            response = get_confident_fixture(prescription_id=prescription_id, image_url=public_image_url)

        # ------------------------------------------------------------------
        # 4. Attach Phase 4 Preprocessing & Quality Extensions
        # ------------------------------------------------------------------
        if quality_report_dict:
            res_metric = quality_report_dict["metrics"]["resolution"]
            contrast_metric = quality_report_dict["metrics"]["contrast"]
            skew_metric = quality_report_dict["metrics"]["skew"]
            response.document_telemetry.estimated_dpi = int(res_metric["effective_ppi"])
            response.document_telemetry.contrast_ratio = float(contrast_metric["rms_contrast"])
            response.document_telemetry.skew_angle_deg = float(skew_metric["estimated_angle_deg"])
            response.document_telemetry.illegibility_score = round(
                float(1.0 - quality_report_dict["heuristic_quality_score"]), 2
            )

        response.processed_image_url = processed_image_url
        response.quality_report = quality_report_dict
        response.preprocessing_manifest = preprocessing_manifest_dict

        return response
