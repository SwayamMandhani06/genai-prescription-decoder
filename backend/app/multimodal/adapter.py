"""
Phase 6: Multimodal Model Adapter
Defines the abstract interface and concrete implementations for multimodal vision-language models:
- IMultimodalModelAdapter (Contract)
- GeminiMultimodalAdapter (Real Vision Model integration via HTTP REST API)
- MockMultimodalModelAdapter (Deterministic test adapter covering all 14 required evaluation scenarios)
"""

import base64
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import httpx

from .config import MultimodalConfig
from .prompts import SYSTEM_INSTRUCTION_V1, USER_INSTRUCTION_V1
from ..schemas.error import ErrorCode
from ..services.pipeline_interface import PipelineProcessingError

logger = logging.getLogger(__name__)


class IMultimodalModelAdapter(ABC):
    """
    Abstract interface for multimodal vision-language model execution.
    Decouples the extraction service from specific cloud or local model providers.
    """

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the adapter has valid credentials/weights and can be invoked."""
        pass

    @abstractmethod
    async def extract(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        config: Optional[MultimodalConfig] = None,
        scenario: Optional[str] = None,
    ) -> str:
        """
        Executes multimodal vision-language inference on raw prescription image bytes.

        Args:
            image_bytes: Raw binary image payload.
            mime_type: Image MIME type ('image/jpeg', 'image/png', etc.).
            config: Multimodal inference configuration.
            scenario: Optional deterministic scenario override for test adapters.

        Returns:
            str: Raw text output from model (expected to contain structured JSON).

        Raises:
            PipelineProcessingError: Standardized error envelope on failure.
        """
        pass


class GeminiMultimodalAdapter(IMultimodalModelAdapter):
    """
    Real multimodal vision-language adapter connecting directly to the Google Gemini
    generateContent API via asynchronous HTTP.
    """

    def __init__(self, config: Optional[MultimodalConfig] = None):
        self.config = config or MultimodalConfig()

    def is_available(self) -> bool:
        api_key = self.config.get_api_key()
        return bool(api_key and len(api_key.strip()) > 5)

    async def extract(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        config: Optional[MultimodalConfig] = None,
        scenario: Optional[str] = None,
    ) -> str:
        active_config = config or self.config
        api_key = active_config.get_api_key()

        if not api_key:
            raise PipelineProcessingError(
                code=ErrorCode.MODEL_UNAVAILABLE,
                message=(
                    f"Multimodal vision model provider '{active_config.provider}' is unavailable: "
                    f"Missing required environment variable '{active_config.api_key_env_var}'."
                ),
                stage="multimodal_inference_dispatch",
                status_code=503,
                retryable=True,
                details={
                    "provider": active_config.provider,
                    "model_id": active_config.model_id,
                    "env_var": active_config.api_key_env_var,
                },
            )

        # Validate input image
        if not image_bytes or len(image_bytes) < 10:
            raise PipelineProcessingError(
                code=ErrorCode.PROCESSING_FAILED,
                message="Cannot perform multimodal extraction: Prescription image payload is empty or invalid.",
                stage="multimodal_input_validation",
                status_code=400,
                retryable=False,
            )

        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{active_config.model_id}:generateContent?key={api_key}"
        )

        request_body = {
            "systemInstruction": {
                "parts": [{"text": SYSTEM_INSTRUCTION_V1}]
            },
            "contents": [
                {
                    "parts": [
                        {"text": USER_INSTRUCTION_V1},
                        {
                            "inlineData": {
                                "mimeType": mime_type,
                                "data": b64_image,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": active_config.temperature,
                "maxOutputTokens": active_config.max_tokens,
                "responseMimeType": "application/json",
            },
        }

        timeout = httpx.Timeout(active_config.timeout_seconds, connect=10.0)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    url,
                    json=request_body,
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": api_key,
                    },
                )

                if response.status_code != 200:
                    error_text = response.text[:400]
                    logger.error(f"Gemini API returned status {response.status_code}: {error_text}")
                    if response.status_code in (401, 403):
                        raise PipelineProcessingError(
                            code=ErrorCode.MODEL_UNAVAILABLE,
                            message=f"Gemini authentication failed ({response.status_code}). Verify GEMINI_API_KEY.",
                            stage="multimodal_inference_dispatch",
                            status_code=503,
                            retryable=True,
                            details={"http_status": response.status_code, "raw_error": error_text},
                        )
                    if response.status_code == 404:
                        raise PipelineProcessingError(
                            code=ErrorCode.MODEL_UNAVAILABLE,
                            message=f"Gemini model '{active_config.model_id}' was not found or is unsupported.",
                            stage="multimodal_inference_dispatch",
                            status_code=503,
                            retryable=False,
                            details={"http_status": response.status_code, "model_id": active_config.model_id, "raw_error": error_text},
                        )
                    if response.status_code in (429, 503, 504):
                        raise PipelineProcessingError(
                            code=ErrorCode.MODEL_UNAVAILABLE,
                            message=f"Gemini multimodal service temporarily unavailable ({response.status_code}).",
                            stage="multimodal_inference_dispatch",
                            status_code=503,
                            retryable=True,
                            details={"http_status": response.status_code, "raw_error": error_text},
                        )
                    raise PipelineProcessingError(
                        code=ErrorCode.PROCESSING_FAILED,
                        message=f"Multimodal inference failed with provider error ({response.status_code}).",
                        stage="multimodal_inference_dispatch",
                        status_code=500,
                        retryable=True,
                        details={"http_status": response.status_code, "raw_error": error_text},
                    )

                data = response.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    raise PipelineProcessingError(
                        code=ErrorCode.PROCESSING_FAILED,
                        message="Multimodal vision model returned no extraction candidates.",
                        stage="multimodal_extraction_decoding",
                        status_code=500,
                        retryable=True,
                    )

                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts or "text" not in parts[0]:
                    raise PipelineProcessingError(
                        code=ErrorCode.PROCESSING_FAILED,
                        message="Multimodal vision model returned empty candidate content.",
                        stage="multimodal_extraction_decoding",
                        status_code=500,
                        retryable=True,
                    )

                return parts[0]["text"]

        except httpx.TimeoutException as exc:
            raise PipelineProcessingError(
                code=ErrorCode.MODEL_UNAVAILABLE,
                message=f"Multimodal vision model request timed out after {active_config.timeout_seconds}s.",
                stage="multimodal_inference_dispatch",
                status_code=504,
                retryable=True,
                details={"timeout_seconds": active_config.timeout_seconds},
            ) from exc
        except httpx.RequestError as exc:
            raise PipelineProcessingError(
                code=ErrorCode.MODEL_UNAVAILABLE,
                message=f"Multimodal network request failed: {str(exc)}",
                stage="multimodal_inference_dispatch",
                status_code=503,
                retryable=True,
            ) from exc


class MockMultimodalModelAdapter(IMultimodalModelAdapter):
    """
    Deterministic test adapter implementing all 14 required Phase 6 evaluation scenarios.
    Ensures complete, reproducible test execution in offline and CI environments.
    """

    def __init__(self, default_scenario: str = "single_medicine_confident"):
        self.default_scenario = default_scenario

    def is_available(self) -> bool:
        return True

    async def extract(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        config: Optional[MultimodalConfig] = None,
        scenario: Optional[str] = None,
    ) -> str:
        active_scenario = (scenario or self.default_scenario).lower().strip()

        # Case 11: Model Unavailable
        if active_scenario in ("model_unavailable", "service_unavailable", "offline"):
            raise PipelineProcessingError(
                code=ErrorCode.MODEL_UNAVAILABLE,
                message="Prescription multimodal vision service is currently unavailable.",
                stage="multimodal_inference_dispatch",
                status_code=503,
                retryable=True,
                details={"provider": "mock", "scenario": active_scenario},
            )

        # Case 12: Processing Failure (corrupt non-JSON text)
        if active_scenario in ("processing_failure", "corrupt_output", "malformed_json"):
            return "<<CORRUPTED RAW OUTPUT - NON JSON STREAM>>"

        # Case 13: Invalid Image
        if active_scenario in ("invalid_image", "unreadable_image"):
            raise PipelineProcessingError(
                code=ErrorCode.PROCESSING_FAILED,
                message="Corrupted or unreadable image stream provided to multimodal adapter.",
                stage="multimodal_input_validation",
                status_code=400,
                retryable=False,
                details={"scenario": active_scenario},
            )

        # Case 14: Empty Extraction Result
        if active_scenario in ("empty_extraction", "blank_page", "empty_result"):
            return json.dumps({
                "medicines": [],
                "requires_human_review": True,
                "visual_observations": "Blank paper or no legible handwritten medication text observed.",
            })

        # Case 1: Single medicine — all fields confident
        if active_scenario in ("single_medicine_confident", "confident", "sample_confident"):
            return json.dumps({
                "medicines": [
                    {
                        "medicine_name": {
                            "value": "Amoxicillin",
                            "status": "confident",
                            "candidates": ["Amoxicillin"],
                            "explanation": "Clear pen stroke in cursive script",
                            "bounding_box": {"x": 12.5, "y": 34.0, "width": 45.0, "height": 8.5},
                        },
                        "dosage": {
                            "value": "500 mg",
                            "status": "confident",
                            "candidates": ["500 mg"],
                            "explanation": "Legible numeral and unit",
                            "bounding_box": {"x": 58.0, "y": 34.0, "width": 18.0, "height": 8.0},
                        },
                        "frequency": {
                            "value": "1-0-1",
                            "status": "confident",
                            "candidates": ["1-0-1"],
                            "explanation": "Distinct dash-delimited schedule notation",
                            "bounding_box": {"x": 77.0, "y": 34.0, "width": 12.0, "height": 7.5},
                        },
                        "duration": {
                            "value": "5 days",
                            "status": "confident",
                            "candidates": ["5 days"],
                            "explanation": "Legible duration string",
                            "bounding_box": {"x": 12.5, "y": 43.0, "width": 20.0, "height": 6.5},
                        },
                        "abbreviations": ["BD", "PC"],
                        "status": "confident",
                        "overall_confidence": 0.96,
                    }
                ],
                "requires_human_review": False,
                "visual_observations": "Prescription pad legible with minimal degradation.",
            })

        # Case 2: Multiple medicines
        if active_scenario in ("multiple_medicines", "multi_med"):
            return json.dumps({
                "medicines": [
                    {
                        "medicine_name": {
                            "value": "Paracetamol",
                            "status": "confident",
                            "candidates": ["Paracetamol"],
                            "explanation": "First line medication item",
                            "bounding_box": {"x": 10.0, "y": 25.0, "width": 40.0, "height": 8.0},
                        },
                        "dosage": {
                            "value": "650 mg",
                            "status": "confident",
                            "candidates": ["650 mg"],
                            "explanation": "Clear dosage",
                            "bounding_box": {"x": 52.0, "y": 25.0, "width": 18.0, "height": 8.0},
                        },
                        "frequency": {
                            "value": "1-1-1",
                            "status": "confident",
                            "candidates": ["1-1-1", "TDS"],
                            "explanation": "Three times daily notation",
                            "bounding_box": {"x": 72.0, "y": 25.0, "width": 15.0, "height": 8.0},
                        },
                        "duration": {
                            "value": "3 days",
                            "status": "confident",
                            "candidates": ["3 days"],
                            "explanation": "Duration stated clearly",
                            "bounding_box": {"x": 10.0, "y": 34.0, "width": 20.0, "height": 6.0},
                        },
                        "abbreviations": ["TDS"],
                        "status": "confident",
                        "overall_confidence": 0.94,
                    },
                    {
                        "medicine_name": {
                            "value": "Cetirizine",
                            "status": "confident",
                            "candidates": ["Cetirizine"],
                            "explanation": "Second line medication item",
                            "bounding_box": {"x": 10.0, "y": 45.0, "width": 38.0, "height": 8.0},
                        },
                        "dosage": {
                            "value": "10 mg",
                            "status": "confident",
                            "candidates": ["10 mg"],
                            "explanation": "Clear dosage strength",
                            "bounding_box": {"x": 50.0, "y": 45.0, "width": 16.0, "height": 8.0},
                        },
                        "frequency": {
                            "value": "0-0-1",
                            "status": "confident",
                            "candidates": ["0-0-1", "HS"],
                            "explanation": "Bedtime frequency notation",
                            "bounding_box": {"x": 68.0, "y": 45.0, "width": 15.0, "height": 8.0},
                        },
                        "duration": {
                            "value": "5 days",
                            "status": "confident",
                            "candidates": ["5 days"],
                            "explanation": "Duration stated clearly",
                            "bounding_box": {"x": 10.0, "y": 54.0, "width": 20.0, "height": 6.0},
                        },
                        "abbreviations": ["HS"],
                        "status": "confident",
                        "overall_confidence": 0.92,
                    }
                ],
                "requires_human_review": False,
                "visual_observations": "Two distinct prescribed medication entries recognized.",
            })

        # Case 3: Missing dosage
        if active_scenario in ("missing_dosage", "no_dosage"):
            return json.dumps({
                "medicines": [
                    {
                        "medicine_name": {
                            "value": "Azithromycin",
                            "status": "confident",
                            "candidates": ["Azithromycin"],
                            "explanation": "Legible drug name",
                            "bounding_box": {"x": 15.0, "y": 30.0, "width": 42.0, "height": 8.0},
                        },
                        "dosage": {
                            "value": None,
                            "status": "uncertain",
                            "presence": "absent",
                            "extraction_state": "missing",
                            "candidates": [],
                            "explanation": "Field is not present in the prescription or cannot be located",
                            "uncertainty_reason": None,
                            "verification_instruction": "Confirm strength (250mg or 500mg) with prescriber",
                            "bounding_box": None,
                        },
                        "frequency": {
                            "value": "1-0-0",
                            "status": "confident",
                            "candidates": ["1-0-0", "OD"],
                            "bounding_box": {"x": 60.0, "y": 30.0, "width": 15.0, "height": 8.0},
                        },
                        "duration": {
                            "value": "3 days",
                            "status": "confident",
                            "candidates": ["3 days"],
                            "bounding_box": {"x": 15.0, "y": 40.0, "width": 20.0, "height": 6.0},
                        },
                        "abbreviations": ["OD"],
                        "status": "uncertain",
                        "overall_confidence": 0.70,
                    }
                ],
                "requires_human_review": True,
                "visual_observations": "Prescription contains Azithromycin without explicit dosage strength.",
            })

        # Case 4: Uncertain medicine name
        if active_scenario in ("uncertain", "uncertain_medicine_name", "uncertain_name", "ambiguous_name"):
            return json.dumps({
                "medicines": [
                    {
                        "medicine_name": {
                            "value": "Amoxcillin",
                            "status": "uncertain",
                            "candidates": ["Amoxcillin", "Ampicillin"],
                            "explanation": "Cursive terminal loop is partially collapsed",
                            "uncertainty_reason": "Ambiguous cursive stroke between -ox- and -pi- ligatures",
                            "verification_instruction": "Inspect physical prescription to verify whether Amoxicillin or Ampicillin was prescribed",
                            "bounding_box": {"x": 14.0, "y": 28.0, "width": 40.0, "height": 9.0},
                        },
                        "dosage": {
                            "value": "500 mg",
                            "status": "confident",
                            "candidates": ["500 mg"],
                            "bounding_box": {"x": 56.0, "y": 28.0, "width": 18.0, "height": 8.0},
                        },
                        "frequency": {
                            "value": "1-0-1",
                            "status": "confident",
                            "candidates": ["1-0-1"],
                            "bounding_box": {"x": 76.0, "y": 28.0, "width": 14.0, "height": 8.0},
                        },
                        "duration": {
                            "value": "5 days",
                            "status": "confident",
                            "candidates": ["5 days"],
                            "bounding_box": {"x": 14.0, "y": 38.0, "width": 20.0, "height": 6.0},
                        },
                        "abbreviations": ["BD"],
                        "status": "uncertain",
                        "overall_confidence": 0.65,
                    }
                ],
                "requires_human_review": True,
                "visual_observations": "Primary medication brand name exhibits severe cursive ambiguity.",
            })

        # Case 5: Uncertain dosage
        if active_scenario in ("uncertain_dosage", "ambiguous_dosage"):
            return json.dumps({
                "medicines": [
                    {
                        "medicine_name": {
                            "value": "Metformin",
                            "status": "confident",
                            "candidates": ["Metformin"],
                            "bounding_box": {"x": 12.0, "y": 32.0, "width": 38.0, "height": 8.0},
                        },
                        "dosage": {
                            "value": "500 mg",
                            "status": "uncertain",
                            "candidates": ["500 mg", "850 mg"],
                            "explanation": "First digit ink loop resembles both '5' and '8'",
                            "uncertainty_reason": "Ambiguous digit stroke in dosage strength",
                            "verification_instruction": "Confirm patient renal profile and intended Metformin dose",
                            "bounding_box": {"x": 52.0, "y": 32.0, "width": 20.0, "height": 8.0},
                        },
                        "frequency": {
                            "value": "1-0-1",
                            "status": "confident",
                            "candidates": ["1-0-1"],
                            "bounding_box": {"x": 74.0, "y": 32.0, "width": 14.0, "height": 8.0},
                        },
                        "duration": {
                            "value": "1 month",
                            "status": "confident",
                            "candidates": ["1 month"],
                            "bounding_box": {"x": 12.0, "y": 42.0, "width": 22.0, "height": 6.0},
                        },
                        "abbreviations": ["BD", "PC"],
                        "status": "uncertain",
                        "overall_confidence": 0.68,
                    }
                ],
                "requires_human_review": True,
                "visual_observations": "Dosage number has ambiguous stroke.",
            })

        # Case 6: Uncertain frequency
        if active_scenario in ("uncertain_frequency", "ambiguous_frequency"):
            return json.dumps({
                "medicines": [
                    {
                        "medicine_name": {
                            "value": "Pantoprazole",
                            "status": "confident",
                            "candidates": ["Pantoprazole"],
                            "bounding_box": {"x": 10.0, "y": 30.0, "width": 42.0, "height": 8.0},
                        },
                        "dosage": {
                            "value": "40 mg",
                            "status": "confident",
                            "candidates": ["40 mg"],
                            "bounding_box": {"x": 54.0, "y": 30.0, "width": 16.0, "height": 8.0},
                        },
                        "frequency": {
                            "value": "1-0-0",
                            "status": "uncertain",
                            "candidates": ["1-0-0", "1-0-1"],
                            "explanation": "Smudged stroke after first numeral",
                            "uncertainty_reason": "Smudge obscures evening slot",
                            "verification_instruction": "Verify once daily vs twice daily administration",
                            "bounding_box": {"x": 72.0, "y": 30.0, "width": 18.0, "height": 8.0},
                        },
                        "duration": {
                            "value": "14 days",
                            "status": "confident",
                            "candidates": ["14 days"],
                            "bounding_box": {"x": 10.0, "y": 40.0, "width": 22.0, "height": 6.0},
                        },
                        "abbreviations": ["OD", "AC"],
                        "status": "uncertain",
                        "overall_confidence": 0.72,
                    }
                ],
                "requires_human_review": True,
                "visual_observations": "Frequency entry exhibits optical smudge.",
            })

        # Case 7: Uncertain duration
        if active_scenario in ("uncertain_duration", "ambiguous_duration"):
            return json.dumps({
                "medicines": [
                    {
                        "medicine_name": {
                            "value": "Augmentin",
                            "status": "confident",
                            "candidates": ["Augmentin"],
                            "bounding_box": {"x": 15.0, "y": 28.0, "width": 38.0, "height": 8.0},
                        },
                        "dosage": {
                            "value": "625 mg",
                            "status": "confident",
                            "candidates": ["625 mg"],
                            "bounding_box": {"x": 55.0, "y": 28.0, "width": 18.0, "height": 8.0},
                        },
                        "frequency": {
                            "value": "1-0-1",
                            "status": "confident",
                            "candidates": ["1-0-1"],
                            "bounding_box": {"x": 75.0, "y": 28.0, "width": 14.0, "height": 8.0},
                        },
                        "duration": {
                            "value": "5 days",
                            "status": "uncertain",
                            "candidates": ["5 days", "7 days"],
                            "explanation": "Numeral top stroke is faint",
                            "uncertainty_reason": "Faint top stroke resembles both 5 and 7",
                            "verification_instruction": "Verify prescribed course length",
                            "bounding_box": {"x": 15.0, "y": 38.0, "width": 20.0, "height": 6.0},
                        },
                        "abbreviations": ["BD", "PC"],
                        "status": "uncertain",
                        "overall_confidence": 0.74,
                    }
                ],
                "requires_human_review": True,
                "visual_observations": "Course duration numeral has faint ink stroke.",
            })

        # Case 8: Abbreviations present
        if active_scenario in ("abbreviations_present", "abbreviations"):
            return json.dumps({
                "medicines": [
                    {
                        "medicine_name": {
                            "value": "Ciprofloxacin",
                            "status": "confident",
                            "candidates": ["Ciprofloxacin"],
                            "bounding_box": {"x": 12.0, "y": 30.0, "width": 42.0, "height": 8.0},
                        },
                        "dosage": {
                            "value": "500 mg",
                            "status": "confident",
                            "candidates": ["500 mg"],
                            "bounding_box": {"x": 56.0, "y": 30.0, "width": 18.0, "height": 8.0},
                        },
                        "frequency": {
                            "value": "1-0-1",
                            "status": "confident",
                            "candidates": ["1-0-1"],
                            "bounding_box": {"x": 76.0, "y": 30.0, "width": 14.0, "height": 8.0},
                        },
                        "duration": {
                            "value": "5 days",
                            "status": "confident",
                            "candidates": ["5 days"],
                            "bounding_box": {"x": 12.0, "y": 40.0, "width": 20.0, "height": 6.0},
                        },
                        "abbreviations": ["BD", "AC", "PC", "SOS"],
                        "status": "confident",
                        "overall_confidence": 0.95,
                    }
                ],
                "requires_human_review": False,
                "visual_observations": "Prescription contains multiple Latin posology abbreviations.",
            })

        # Case 9: Multiple uncertain fields
        if active_scenario in ("multiple_uncertain_fields", "multiple_uncertain"):
            return json.dumps({
                "medicines": [
                    {
                        "medicine_name": {
                            "value": "Cefixime",
                            "status": "uncertain",
                            "candidates": ["Cefixime", "Cefuroxime"],
                            "explanation": "Severe handwriting degradation",
                            "uncertainty_reason": "Collapsed vowels and ligature",
                            "verification_instruction": "Pharmacist must contact prescriber for clarification",
                            "bounding_box": {"x": 10.0, "y": 25.0, "width": 40.0, "height": 9.0},
                        },
                        "dosage": {
                            "value": "200 mg",
                            "status": "uncertain",
                            "candidates": ["200 mg", "400 mg"],
                            "explanation": "First digit smudged",
                            "uncertainty_reason": "Smudge across numeral",
                            "verification_instruction": "Confirm dosage strength",
                            "bounding_box": {"x": 52.0, "y": 25.0, "width": 18.0, "height": 8.0},
                        },
                        "frequency": {
                            "value": "1-0-1",
                            "status": "uncertain",
                            "candidates": ["1-0-1", "1-0-0"],
                            "explanation": "Indistinct final numeral",
                            "uncertainty_reason": "Faint stroke",
                            "verification_instruction": "Verify daily frequency",
                            "bounding_box": {"x": 72.0, "y": 25.0, "width": 16.0, "height": 8.0},
                        },
                        "duration": {
                            "value": "5 days",
                            "status": "confident",
                            "candidates": ["5 days"],
                            "bounding_box": {"x": 10.0, "y": 36.0, "width": 20.0, "height": 6.0},
                        },
                        "abbreviations": ["BD"],
                        "status": "uncertain",
                        "overall_confidence": 0.45,
                    }
                ],
                "requires_human_review": True,
                "visual_observations": "Multiple posology fields are visually ambiguous.",
            })

        # Case 10: Human-review-required case
        if active_scenario in ("human_review_required", "review_required", "flagged"):
            return json.dumps({
                "medicines": [
                    {
                        "medicine_name": {
                            "value": "Atorvastatin",
                            "status": "confident",
                            "candidates": ["Atorvastatin"],
                            "bounding_box": {"x": 14.0, "y": 30.0, "width": 40.0, "height": 8.0},
                        },
                        "dosage": {
                            "value": "80 mg",
                            "status": "flagged",
                            "candidates": ["80 mg", "10 mg"],
                            "explanation": "High potency statin dose with ambiguous first digit",
                            "uncertainty_reason": "Significant clinical risk if 10mg was intended instead of 80mg",
                            "verification_instruction": "Mandatory pharmacist verification before dispensing",
                            "bounding_box": {"x": 56.0, "y": 30.0, "width": 18.0, "height": 8.0},
                        },
                        "frequency": {
                            "value": "0-0-1",
                            "status": "confident",
                            "candidates": ["0-0-1", "HS"],
                            "bounding_box": {"x": 76.0, "y": 30.0, "width": 14.0, "height": 8.0},
                        },
                        "duration": {
                            "value": "30 days",
                            "status": "confident",
                            "candidates": ["30 days"],
                            "bounding_box": {"x": 14.0, "y": 40.0, "width": 22.0, "height": 6.0},
                        },
                        "abbreviations": ["HS"],
                        "status": "flagged",
                        "overall_confidence": 0.50,
                    }
                ],
                "requires_human_review": True,
                "visual_observations": "High-risk dosage discrepancy requires human clinical confirmation.",
            })

        # Default fallback: single medicine confident
        return json.dumps({
            "medicines": [
                {
                    "medicine_name": {
                        "value": "Amoxicillin",
                        "status": "confident",
                        "candidates": ["Amoxicillin"],
                        "bounding_box": {"x": 12.5, "y": 34.0, "width": 45.0, "height": 8.5},
                    },
                    "dosage": {
                        "value": "500 mg",
                        "status": "confident",
                        "candidates": ["500 mg"],
                        "bounding_box": {"x": 58.0, "y": 34.0, "width": 18.0, "height": 8.0},
                    },
                    "frequency": {
                        "value": "1-0-1",
                        "status": "confident",
                        "candidates": ["1-0-1"],
                        "bounding_box": {"x": 77.0, "y": 34.0, "width": 12.0, "height": 7.5},
                    },
                    "duration": {
                        "value": "5 days",
                        "status": "confident",
                        "candidates": ["5 days"],
                        "bounding_box": {"x": 12.5, "y": 43.0, "width": 20.0, "height": 6.5},
                    },
                    "abbreviations": ["BD", "PC"],
                    "status": "confident",
                    "overall_confidence": 0.95,
                }
            ],
            "requires_human_review": False,
            "visual_observations": "Deterministic mock extraction executed.",
        })
