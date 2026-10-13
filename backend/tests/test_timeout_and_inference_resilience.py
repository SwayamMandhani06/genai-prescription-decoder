"""
Regression Test Suite: Pipeline Timeouts, Upstream Resilience & Safe Stage Timing Telemetry

Covers Requirement 9:
1. Slow inference within bounded timeout succeeds.
2. Upstream Gemini timeout (httpx.TimeoutException) returns HTTP 504 Gateway Timeout.
3. Upstream provider errors (503 Service Unavailable, 429 Rate Limit, 500 Server Error) return explicit safe errors.
4. Live inference mode strictly never falls back to mock fixtures or hardcoded data on error.
5. Structured stage timing telemetry is logged for every stage without leaking patient, clinical, or secret data.
"""

import io
import json
import logging
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.config import get_settings
from backend.app.multimodal.config import MultimodalConfig
from backend.app.multimodal.adapter import GeminiMultimodalAdapter
from backend.app.services.multimodal_pipeline import MultimodalPrescriptionPipeline
from backend.app.services.pipeline_interface import PipelineOptions, PipelineProcessingError
from backend.app.schemas.error import ErrorCode


def create_test_image_bytes() -> bytes:
    """Loads a genuine test sample image that passes pre-processing quality assessment."""
    sample_path = Path("data/samples/sample_01_clear.png")
    if sample_path.exists():
        return sample_path.read_bytes()
    from PIL import Image, ImageDraw
    buf = io.BytesIO()
    img = Image.new("RGB", (300, 300), color=(240, 240, 240))
    d = ImageDraw.Draw(img)
    d.text((20, 50), "Augmentin 625mg 1 tab bid", fill=(20, 20, 20))
    img.save(buf, format="PNG")
    return buf.getvalue()


VALID_GEMINI_EXTRACTION_JSON = json.dumps({
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


class TestTimeoutAndInferenceResilience:
    """Verifies timeout boundaries, upstream failure handling, and structured telemetry."""

    def test_upstream_gemini_timeout_returns_http_504(self):
        """When the upstream Gemini vision request times out, return HTTP 504 Gateway Timeout."""
        test_settings = get_settings().model_copy(update={
            "USE_MOCK_PIPELINE": False,
            "GEMINI_API_KEY": "AIzaSyFakeKeyForTimeoutTest1234567890",
        })
        app.dependency_overrides[get_settings] = lambda: test_settings

        try:
            with patch.dict("os.environ", {"GEMINI_API_KEY": "AIzaSyFakeKeyForTimeoutTest1234567890"}), \
                 patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Request timed out after 50.0s")):
                
                client = TestClient(app)
                img_bytes = create_test_image_bytes()
                response = client.post(
                    "/api/v1/prescriptions/analyze",
                    files={"file": ("sample.png", img_bytes, "image/png")},
                )

                assert response.status_code == 504, f"Expected 504 Gateway Timeout, got {response.status_code}"
                body = response.json()
                assert "error" in body
                assert body["error"]["code"] == ErrorCode.MODEL_UNAVAILABLE
                assert "timed out" in body["error"]["message"].lower()
                assert body["error"]["retryable"] is True
                # Crucial: prove no mock data or medicines returned
                assert "data" not in body
                assert "medicines" not in body
        finally:
            app.dependency_overrides.pop(get_settings, None)

    def test_upstream_gemini_503_high_demand_returns_http_503(self):
        """When Gemini returns 503 (demand spike), adapter surfaces HTTP 503 without fallback to mock."""
        test_settings = get_settings().model_copy(update={
            "USE_MOCK_PIPELINE": False,
            "GEMINI_API_KEY": "AIzaSyFakeKeyForTimeoutTest1234567890",
        })
        app.dependency_overrides[get_settings] = lambda: test_settings

        mock_resp = MagicMock()
        mock_resp.status_code = 503
        mock_resp.text = json.dumps({
            "error": {
                "code": 503,
                "message": "This model is currently experiencing high demand. Please try again later.",
                "status": "UNAVAILABLE",
            }
        })

        try:
            with patch.dict("os.environ", {"GEMINI_API_KEY": "AIzaSyFakeKeyForTimeoutTest1234567890"}), \
                 patch("httpx.AsyncClient.post", return_value=mock_resp), \
                 patch("asyncio.sleep", new_callable=AsyncMock):  # make retry instantaneous in test
                
                client = TestClient(app)
                img_bytes = create_test_image_bytes()
                response = client.post(
                    "/api/v1/prescriptions/analyze",
                    files={"file": ("sample.png", img_bytes, "image/png")},
                )

                assert response.status_code == 503
                body = response.json()
                assert body["error"]["code"] == ErrorCode.MODEL_UNAVAILABLE
                assert "503" in body["error"]["message"] or "unavailable" in body["error"]["message"].lower()
                assert body["error"]["retryable"] is True
                assert "data" not in body
        finally:
            app.dependency_overrides.pop(get_settings, None)

    def test_upstream_gemini_429_rate_limit_returns_http_503(self):
        """When Gemini returns 429 rate limit, returns HTTP 503 retryable without mock fallback."""
        test_settings = get_settings().model_copy(update={
            "USE_MOCK_PIPELINE": False,
            "GEMINI_API_KEY": "AIzaSyFakeKeyForTimeoutTest1234567890",
        })
        app.dependency_overrides[get_settings] = lambda: test_settings

        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.text = '{"error": {"code": 429, "message": "Resource has been exhausted (quota)."}}'

        try:
            with patch.dict("os.environ", {"GEMINI_API_KEY": "AIzaSyFakeKeyForTimeoutTest1234567890"}), \
                 patch("httpx.AsyncClient.post", return_value=mock_resp), \
                 patch("asyncio.sleep", new_callable=AsyncMock):
                
                client = TestClient(app)
                img_bytes = create_test_image_bytes()
                response = client.post(
                    "/api/v1/prescriptions/analyze",
                    files={"file": ("sample.png", img_bytes, "image/png")},
                )

                assert response.status_code == 503
                body = response.json()
                assert body["error"]["code"] == ErrorCode.MODEL_UNAVAILABLE
                assert body["error"]["retryable"] is True
                assert "data" not in body
        finally:
            app.dependency_overrides.pop(get_settings, None)

    def test_slow_inference_within_timeout_completes_successfully(self):
        """When inference succeeds after a delay (slow inference), pipeline finishes with HTTP 200."""
        test_settings = get_settings().model_copy(update={
            "USE_MOCK_PIPELINE": False,
            "GEMINI_API_KEY": "AIzaSyFakeKeyForTimeoutTest1234567890",
        })
        app.dependency_overrides[get_settings] = lambda: test_settings

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": VALID_GEMINI_EXTRACTION_JSON}]
                    }
                }
            ]
        }

        async def delayed_post(*args, **kwargs):
            import asyncio
            await asyncio.sleep(0.05)  # Simulate slow inference
            return mock_resp

        try:
            with patch.dict("os.environ", {"GEMINI_API_KEY": "AIzaSyFakeKeyForTimeoutTest1234567890"}), \
                 patch("httpx.AsyncClient.post", side_effect=delayed_post):
                
                client = TestClient(app)
                img_bytes = create_test_image_bytes()
                response = client.post(
                    "/api/v1/prescriptions/analyze",
                    files={"file": ("sample.png", img_bytes, "image/png")},
                )

                assert response.status_code == 200
                body = response.json()
                assert body["status"] == "success"
                assert "meta" in body
                assert body["meta"]["processing_time_ms"] > 0
                assert body["meta"]["model_version"] in ("gemini:gemini-3.8-flash", "gemini:gemini-3.6-flash", "gemini:gemini-3.5-flash-lite")
                assert len(body["medicines"]) == 1
                assert body["medicines"][0]["medicine_name"]["value"] == "Amoxicillin"
        finally:
            app.dependency_overrides.pop(get_settings, None)

    @pytest.mark.asyncio
    async def test_structured_stage_timing_logging_and_privacy(self, caplog):
        """Proves each pipeline stage is measured and logged safely without leaking sensitive data."""
        pipeline = MultimodalPrescriptionPipeline()
        img_bytes = create_test_image_bytes()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": VALID_GEMINI_EXTRACTION_JSON}]
                    }
                }
            ]
        }

        with caplog.at_level(logging.INFO), \
             patch.dict("os.environ", {"GEMINI_API_KEY": "AIzaSyFakeKeyForTimeoutTest1234567890"}), \
             patch("httpx.AsyncClient.post", return_value=mock_resp):
            
            res = await pipeline.process_prescription(
                image_bytes=img_bytes,
                filename="sample.png",
                public_image_url="/uploads/samples/sample_01_clear.png",
                options=PipelineOptions(confidence_threshold=0.65, enable_lasa_detection=True, target_language="en"),
            )

            assert res.status == "success"
            assert res.meta.processing_time_ms > 0

            # Find timing log in caplog
            timing_logs = [record.message for record in caplog.records if "processing timings" in record.message]
            assert len(timing_logs) >= 1, "Expected structured processing timings log record"
            timing_log = timing_logs[0]

            assert "preprocessing=" in timing_log
            assert "inference=" in timing_log
            assert "rag=" in timing_log
            assert "confidence=" in timing_log
            assert "lasa=" in timing_log
            assert "abstention=" in timing_log
            assert "explanation=" in timing_log
            assert "total=" in timing_log

            # Privacy and security verification: no API keys, patient details, or medicine content leaked in timing logs
            assert "AIza" not in timing_log
            assert "Amoxicillin" not in timing_log
            assert "patient" not in timing_log.lower()
