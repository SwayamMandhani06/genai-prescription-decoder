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
        # 2. Deterministic Scenario Matching (options.mock_scenario or sample_id)
        # ------------------------------------------------------------------
        if scenario == "uncertain":
            return get_uncertain_fixture(prescription_id=prescription_id, image_url=public_image_url)

        if scenario == "lasa_warning" or sample_id == "rx-sample-2":
            return get_lasa_fixture(prescription_id=prescription_id, image_url=public_image_url)

        if scenario in ("abstained", "flagged") or sample_id == "rx-sample-3":
            return get_abstained_fixture(prescription_id=prescription_id, image_url=public_image_url)

        # Default to confident scenario
        return get_confident_fixture(prescription_id=prescription_id, image_url=public_image_url)
