"""
Phase 6: Multimodal Vision-Language Extraction Service
Orchestrates end-to-end multimodal prescription posology extraction:
- Ingests untouched original prescription image bytes
- Dispatches to configured multimodal model adapter (Gemini or deterministic Mock)
- Parses structured response with strict code fence and schema validation
- Computes cryptographic SHA-256 audit hashes for input and derived artifacts
- Applies conservative post-processing to ensure no hallucination or medical guessing
- Preserves full research traceability metadata according to PLAN.md Section 19.
"""

import hashlib
import time
from typing import Optional

from .adapter import IMultimodalModelAdapter, GeminiMultimodalAdapter, MockMultimodalModelAdapter
from .config import MultimodalConfig
from .parser import parse_multimodal_response
from .postprocess import finalize_extraction_result
from .schemas import ModelMetadata, PrescriptionExtractionResult
from ..schemas.error import ErrorCode
from ..services.pipeline_interface import PipelineProcessingError


class MultimodalExtractionService:
    """
    Central orchestration service for Phase 6 Multimodal Vision-Language Extraction.
    """

    def __init__(
        self,
        adapter: Optional[IMultimodalModelAdapter] = None,
        config: Optional[MultimodalConfig] = None,
    ):
        self.config = config or MultimodalConfig()
        if adapter is not None:
            self.adapter = adapter
        elif self.config.provider == "gemini":
            self.adapter = GeminiMultimodalAdapter(config=self.config)
        else:
            self.adapter = MockMultimodalModelAdapter()

    async def extract_prescription(
        self,
        image_bytes: bytes,
        prescription_id: str,
        original_image_url: str,
        mime_type: str = "image/jpeg",
        preprocessed_bytes: Optional[bytes] = None,
        preprocessed_image_url: Optional[str] = None,
        scenario: Optional[str] = None,
    ) -> PrescriptionExtractionResult:
        """
        Executes multimodal vision-language prescription extraction.

        Args:
            image_bytes: Raw bytes of untouched original prescription image.
            prescription_id: Statutory tracking identifier.
            original_image_url: Public/storage URL of original image.
            mime_type: Image MIME type ('image/jpeg', 'image/png').
            preprocessed_bytes: Optional bytes of Phase 4 preprocessed image.
            preprocessed_image_url: Optional URL of Phase 4 preprocessed image.
            scenario: Optional test scenario for deterministic mock adapter.

        Returns:
            PrescriptionExtractionResult: Complete typed structured extraction.
        """
        if not image_bytes or len(image_bytes) < 10:
            raise PipelineProcessingError(
                code=ErrorCode.PROCESSING_FAILED,
                message="Cannot perform multimodal extraction: Image payload is empty or invalid.",
                stage="multimodal_input_validation",
                status_code=400,
                retryable=False,
                prescription_id=prescription_id,
                original_image_url=original_image_url,
            )

        # 1. Cryptographic SHA-256 fingerprints for research traceability
        source_sha256 = hashlib.sha256(image_bytes).hexdigest()
        preprocessed_sha256 = (
            hashlib.sha256(preprocessed_bytes).hexdigest()
            if preprocessed_bytes
            else None
        )

        start_time = time.perf_counter()

        # 2. Invoke multimodal model adapter
        raw_text = await self.adapter.extract(
            image_bytes=image_bytes,
            mime_type=mime_type,
            config=self.config,
            scenario=scenario,
        )

        # 3. Parse model output into structured representations
        try:
            parsed = parse_multimodal_response(raw_text, source="original_image")
        except Exception as exc:
            # Map parse errors to pipeline processing errors
            raise PipelineProcessingError(
                code=ErrorCode.PROCESSING_FAILED,
                message=f"Multimodal vision model output parsing failed: {str(exc)}",
                stage="multimodal_response_parsing",
                status_code=500,
                retryable=True,
                details={"raw_response_snippet": str(raw_text)[:300]},
                prescription_id=prescription_id,
                original_image_url=original_image_url,
            ) from exc

        duration = time.perf_counter() - start_time

        # 4. Construct audit metadata
        is_mock = isinstance(self.adapter, MockMultimodalModelAdapter) or self.config.provider == "mock"
        model_meta = ModelMetadata(
            provider="mock" if is_mock else self.config.provider,
            model_id="mock-prescription-v1" if is_mock else self.config.model_id,
            model_version="mock-v1" if is_mock else self.config.model_version,
            prompt_version=self.config.prompt_version,
            config_version=self.config.config_version,
            is_mock=is_mock,
        )

        # 5. Finalize with conservative post-processing
        result = finalize_extraction_result(
            prescription_id=prescription_id,
            original_image_url=original_image_url,
            source_image_sha256=source_sha256,
            medicines=parsed["medicines"],
            model_metadata=model_meta,
            duration_seconds=duration,
            raw_model_response=raw_text,
            preprocessed_image_url=preprocessed_image_url,
            preprocessed_image_sha256=preprocessed_sha256,
            model_demands_review=parsed["requires_human_review"],
        )

        return result
