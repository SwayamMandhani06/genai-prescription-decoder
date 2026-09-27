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
        elif scenario == "lasa_warning" or sample_id in ("rx-sample-2", "sample-2"):
            response = get_lasa_fixture(prescription_id=prescription_id, image_url=public_image_url)
        elif scenario in ("abstained", "flagged") or sample_id in ("rx-sample-3", "sample-3"):
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

        # ------------------------------------------------------------------
        # 5. Attach Phase 8 Confidence Assessment & Field Enrichment
        # ------------------------------------------------------------------
        from ai.confidence.service import get_confidence_service

        conf_service = get_confidence_service()

        for f_key, f_item in response.fields.items():
            if f_item.raw_confidence is None:
                f_item.raw_confidence = f_item.confidence
            if not f_item.calibration_status:
                f_item.calibration_status = conf_service.calibration_status
            if not f_item.calibration_method:
                f_item.calibration_method = conf_service.active_method

        if response.confidence_assessment is None:
            response.confidence_assessment = {
                "prescription_id": prescription_id,
                "overall_raw_score": response.data.document_confidence if response.data else 0.85,
                "overall_calibrated_confidence": None,
                "calibration_status": conf_service.calibration_status,
                "calibration_method": conf_service.active_method,
                "medicines": [],
            }

        # ------------------------------------------------------------------
        # 6. Attach Phase 9 Abstention Determination & Human Verification
        # ------------------------------------------------------------------
        from ai.abstention.service import get_abstention_service

        abstention_service = get_abstention_service()
        response.meta.pipeline_stages_completed = 9

        abstained_keys = []
        for f_key, f_item in response.fields.items():
            is_abstained = False
            reasons = []
            if f_item.status in ("uncertain", "flagged"):
                is_abstained = True
                if f_item.status == "uncertain":
                    reasons.append("EXTRACTION_UNCERTAIN")
                if f_item.status == "flagged":
                    reasons.append("AMBIGUOUS_CURSIVE_STROKE")
            elif getattr(f_item, "candidates", None) and len(f_item.candidates) > 1:
                is_abstained = True
                reasons.append("MULTIPLE_CANDIDATES")

            # Check if overall response requires review/abstain or has validation flags
            if (response.requires_human_review or response.status == "abstain") and f_key in ("medicine_name", "medication"):
                is_abstained = True
                if "VALIDATION_CONFLICT" not in reasons:
                    reasons.append("VALIDATION_CONFLICT")

            if is_abstained:
                if f_item.calibration_status == "insufficient_data" and "CALIBRATION_INSUFFICIENT_DATA" not in reasons:
                    reasons.append("CALIBRATION_INSUFFICIENT_DATA")
                f_item.abstention_decision = "abstained"
                f_item.abstention_reasons = reasons
                f_item.requires_human_verification = True
                abstained_keys.append(f_key)
            else:
                f_item.abstention_decision = "accepted"
                f_item.abstention_reasons = []
                f_item.requires_human_verification = False

        if response.requires_human_review and not abstained_keys:
            abstained_keys.append("medicine_name")

        requires_verification = len(abstained_keys) > 0 or response.requires_human_review is True
        presc_decision = "REQUIRES_HUMAN_VERIFICATION" if requires_verification else "ACCEPTED"

        if response.abstention is None:
            response.abstention = {
                "prescription_id": prescription_id,
                "policy_version": abstention_service.config.policy_version,
                "prescription_decision": presc_decision,
                "requires_human_verification": requires_verification,
                "fields_requiring_verification": abstained_keys,
                "total_fields_evaluated": len(response.fields),
                "abstained_fields_count": len(abstained_keys),
                "abstention_rate": round(len(abstained_keys) / len(response.fields), 4) if response.fields else 0.0,
                "summary": (
                    f"Prescription requires human verification: {len(abstained_keys)} fields abstained."
                    if requires_verification
                    else "All posology fields accepted under active policy."
                ),
                "config_hash": abstention_service.config.get_config_hash(),
            }

        # Ensure verification state is registered
        abstention_service.get_or_create_verification_state(
            prescription_id=prescription_id,
            original_image_url=response.original_image_url or "",
            pending_fields=abstained_keys,
        )

        return response
