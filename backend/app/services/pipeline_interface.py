"""
Abstract Pipeline Interface for AURA-Rx Prescription Understanding
Establishes the decoupled service boundary required by PLAN.md Section 5.3 & Section 11.
Future AI modules (OCR, Multimodal Swin/LLM, RAG, LASA, Multilingual) will implement this interface
without breaking the API routes or client contracts.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field
from ..schemas.prescription import PrescriptionAnalyzeResponse
from ..schemas.error import ErrorCode


class PipelineOptions(BaseModel):
    """Execution parameters passed into the pipeline."""
    confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    enable_lasa_detection: bool = Field(True)
    target_language: str = Field("en")
    mock_scenario: Optional[str] = Field(None)
    sample_id: Optional[str] = Field(None)


class PipelineProcessingError(Exception):
    """
    Standard domain exception raised by pipeline implementations.
    Converts directly to the PLAN.md Section 6 ErrorResponse envelope.
    """
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        stage: str = "multimodal_extraction",
        status_code: int = 500,
        retryable: bool = True,
        details: Optional[Dict[str, Any]] = None,
        prescription_id: Optional[str] = None,
        original_image_url: Optional[str] = None,
    ):
        self.code = code
        self.message = message
        self.stage = stage
        self.status_code = status_code
        self.retryable = retryable
        self.details = details or {}
        self.prescription_id = prescription_id
        self.original_image_url = original_image_url
        super().__init__(message)


class IPrescriptionPipeline(ABC):
    """
    Formal interface for all prescription processing pipelines (Mock and Live Multimodal AI).
    """

    @abstractmethod
    async def process_prescription(
        self,
        image_bytes: Optional[bytes],
        filename: Optional[str],
        public_image_url: str,
        options: PipelineOptions,
    ) -> PrescriptionAnalyzeResponse:
        """
        Processes a prescription document and returns structured, evidence-grounded posology.

        Args:
            image_bytes: Raw bytes of the uploaded prescription image (if uploaded).
            filename: Client-provided filename.
            public_image_url: Stored URL of the preserved original image.
            options: Pipeline options (confidence thresholds, language, mock scenarios).

        Returns:
            PrescriptionAnalyzeResponse: Structured posology matching Section 6 & Phase 1 DTOs.

        Raises:
            PipelineProcessingError: Standardized error envelope on failure.
        """
        pass
