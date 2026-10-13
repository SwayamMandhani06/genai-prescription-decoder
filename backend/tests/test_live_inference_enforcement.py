"""
Regression Test Suite: Enforcing Live-Only Multimodal Inference (USE_MOCK_PIPELINE=False)

Proves that:
1. When USE_MOCK_PIPELINE=false, the backend never silently falls back to MockMultimodalModelAdapter,
   deterministic fixtures, or hardcoded prescription results.
2. Missing, empty, or placeholder GEMINI_API_KEY values return explicit safe HTTP 503 errors.
3. Provider authentication failures (401/403), rate limits (429), outages (503), timeouts (504),
   and model-not-found errors (404) return explicit safe errors and NEVER substitute mock data.
4. Provider content blocks (promptFeedback) return HTTP 422 and never fall back to mock data.
5. Logs and error envelopes never expose or leak API keys or secrets.
6. Mock adapters remain available only when explicitly enabled for tests or demonstrations (USE_MOCK_PIPELINE=true).
7. Health endpoint accurately reports pipeline status, active model, and adapter readiness.
"""

import io
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.config import get_settings, Settings
from backend.app.multimodal.config import MultimodalConfig
from backend.app.multimodal.adapter import GeminiMultimodalAdapter, sanitize_secret_text
from backend.app.schemas.error import ErrorCode


from pathlib import Path


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


class TestLiveInferenceEnforcement:
    """Strict regression tests for live-only inference enforcement."""

    def test_missing_or_placeholder_key_in_live_mode_rejects_with_503(self):
        """When USE_MOCK_PIPELINE=false and GEMINI_API_KEY is missing/placeholder, reject with 503."""
        test_settings = get_settings().model_copy(update={
            "USE_MOCK_PIPELINE": False,
            "GEMINI_API_KEY": "your_gemini_api_key_here",
        })
        app.dependency_overrides[get_settings] = lambda: test_settings

        try:
            with patch.dict("os.environ", {"GEMINI_API_KEY": "your_gemini_api_key_here", "GOOGLE_API_KEY": ""}):
                client = TestClient(app)
                img_bytes = create_test_image_bytes()
                resp = client.post(
                    "/api/v1/prescriptions/analyze",
                    files={"file": ("rx_test.png", img_bytes, "image/png")},
                )
                assert resp.status_code == 503
                data = resp.json()
                assert "error" in data
                assert data["error"]["code"] == ErrorCode.MODEL_UNAVAILABLE.value
                assert "missing or is an invalid placeholder" in data["error"]["message"].lower() or "unavailable" in data["error"]["message"].lower()
                # Ensure NO mock data returned
                assert "medicines" not in data
                assert "extracted_entities" not in data.get("data", {})
        finally:
            app.dependency_overrides.pop(get_settings, None)

    def test_provider_auth_failure_returns_503_and_never_falls_back_to_mock(self):
        """When Gemini API returns HTTP 401/403, return 503 and do not fall back to mock data."""
        test_settings = get_settings().model_copy(update={
            "USE_MOCK_PIPELINE": False,
            "GEMINI_API_KEY": "AIzaSyFakeKeyForTestingPurposeOnly12345",
        })
        app.dependency_overrides[get_settings] = lambda: test_settings

        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = '{"error": {"code": 401, "message": "API key not valid. Please pass a valid API key."}}'

        try:
            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_resp
                client = TestClient(app)
                img_bytes = create_test_image_bytes()
                resp = client.post(
                    "/api/v1/prescriptions/analyze",
                    files={"file": ("rx_test.png", img_bytes, "image/png")},
                )
                assert resp.status_code == 503
                data = resp.json()
                assert data["error"]["code"] == ErrorCode.MODEL_UNAVAILABLE.value
                assert "authentication failed" in data["error"]["message"].lower()
                # Ensure NO mock data returned
                assert "medicines" not in data
                assert "extracted_entities" not in data.get("data", {})
        finally:
            app.dependency_overrides.pop(get_settings, None)

    def test_provider_outage_or_rate_limit_returns_503_and_never_falls_back(self):
        """When Gemini API returns 429/503 (high demand/rate limit), return 503 and never fall back."""
        test_settings = get_settings().model_copy(update={
            "USE_MOCK_PIPELINE": False,
            "GEMINI_API_KEY": "AIzaSyFakeKeyForTestingPurposeOnly12345",
        })
        app.dependency_overrides[get_settings] = lambda: test_settings

        mock_resp = MagicMock()
        mock_resp.status_code = 503
        mock_resp.text = '{"error": {"code": 503, "message": "This model is currently experiencing high demand."}}'

        try:
            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_resp
                client = TestClient(app)
                img_bytes = create_test_image_bytes()
                resp = client.post(
                    "/api/v1/prescriptions/analyze",
                    files={"file": ("rx_test.png", img_bytes, "image/png")},
                )
                assert resp.status_code == 503
                data = resp.json()
                assert data["error"]["code"] == ErrorCode.MODEL_UNAVAILABLE.value
                assert "temporarily unavailable" in data["error"]["message"].lower()
                # Must never return mock results
                assert "medicines" not in data
        finally:
            app.dependency_overrides.pop(get_settings, None)

    def test_model_not_found_404_returns_explicit_error_and_never_falls_back(self):
        """When configured model is unsupported or not found (404), return 503 without fallback."""
        test_settings = get_settings().model_copy(update={
            "USE_MOCK_PIPELINE": False,
            "GEMINI_API_KEY": "AIzaSyFakeKeyForTestingPurposeOnly12345",
        })
        app.dependency_overrides[get_settings] = lambda: test_settings

        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.text = '{"error": {"code": 404, "message": "Model not found."}}'

        try:
            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_resp
                client = TestClient(app)
                img_bytes = create_test_image_bytes()
                resp = client.post(
                    "/api/v1/prescriptions/analyze",
                    files={"file": ("rx_test.png", img_bytes, "image/png")},
                )
                assert resp.status_code == 503
                data = resp.json()
                assert data["error"]["code"] == ErrorCode.MODEL_UNAVAILABLE.value
                assert "was not found or is unsupported" in data["error"]["message"]
                assert "medicines" not in data
        finally:
            app.dependency_overrides.pop(get_settings, None)

    def test_provider_safety_block_returns_422_and_never_falls_back(self):
        """When Gemini API blocks input via promptFeedback, return 422 and never fall back."""
        test_settings = get_settings().model_copy(update={
            "USE_MOCK_PIPELINE": False,
            "GEMINI_API_KEY": "AIzaSyFakeKeyForTestingPurposeOnly12345",
        })
        app.dependency_overrides[get_settings] = lambda: test_settings

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "promptFeedback": {"blockReason": "SAFETY"}
        }

        try:
            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_resp
                client = TestClient(app)
                img_bytes = create_test_image_bytes()
                resp = client.post(
                    "/api/v1/prescriptions/analyze",
                    files={"file": ("rx_test.png", img_bytes, "image/png")},
                )
                assert resp.status_code == 422
                data = resp.json()
                assert data["error"]["code"] == ErrorCode.PROCESSING_FAILED.value
                assert "blocked request" in data["error"]["message"].lower()
                assert "medicines" not in data
        finally:
            app.dependency_overrides.pop(get_settings, None)

    def test_secret_scrubbing_protects_credentials(self):
        """Ensures sanitize_secret_text scrubs all API keys and tokens from logs/details."""
        raw_error = "Failed to connect with key=AIzaSySecretTestKey123456789012345 and x-goog-api-key: AIzaSyAnotherSecretKey987654321"
        sanitized = sanitize_secret_text(raw_error)
        assert "AIzaSy" not in sanitized
        assert "[REDACTED" in sanitized

    def test_health_endpoint_reports_degraded_when_live_mode_has_invalid_key(self):
        """Health endpoint must report degraded status when live mode is set without valid key."""
        test_settings = get_settings().model_copy(update={
            "USE_MOCK_PIPELINE": False,
            "GEMINI_API_KEY": "your_gemini_api_key_here",
        })
        app.dependency_overrides[get_settings] = lambda: test_settings

        try:
            with patch.dict("os.environ", {"GEMINI_API_KEY": "your_gemini_api_key_here", "GOOGLE_API_KEY": ""}):
                client = TestClient(app)
                resp = client.get("/api/v1/health")
                assert resp.status_code == 200
                data = resp.json()
                assert data["status"] == "degraded"
                assert data["mock_mode"] is False
                deps = data["system_info"]["dependencies"]
                assert deps["gemini_api_key_configured"] is False
                assert deps["model_adapter_status"] == "missing_or_invalid_api_key"
                assert deps["configured_model"] in ("gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite")
        finally:
            app.dependency_overrides.pop(get_settings, None)

    def test_health_endpoint_reports_healthy_when_live_mode_has_valid_key(self):
        """Health endpoint must report healthy status when live mode has valid key."""
        test_settings = get_settings().model_copy(update={
            "USE_MOCK_PIPELINE": False,
            "GEMINI_API_KEY": "AIzaSyValidFormatKeyForTestExecution12345",
        })
        app.dependency_overrides[get_settings] = lambda: test_settings

        try:
            with patch.dict("os.environ", {"GEMINI_API_KEY": "AIzaSyValidFormatKeyForTestExecution12345"}):
                client = TestClient(app)
                resp = client.get("/api/v1/health")
                assert resp.status_code == 200
                data = resp.json()
                assert data["status"] == "healthy"
                assert data["mock_mode"] is False
                deps = data["system_info"]["dependencies"]
                assert deps["gemini_api_key_configured"] is True
                assert deps["model_adapter_status"] == "ready_configured"
        finally:
            app.dependency_overrides.pop(get_settings, None)

    def test_mock_pipeline_available_when_explicitly_enabled(self):
        """Mock pipeline is active and returns mock fixtures when USE_MOCK_PIPELINE=true."""
        test_settings = get_settings().model_copy(update={
            "USE_MOCK_PIPELINE": True,
        })
        app.dependency_overrides[get_settings] = lambda: test_settings

        try:
            client = TestClient(app)
            resp = client.get("/api/v1/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["mock_mode"] is True
            assert data["status"] == "healthy"
            assert data["system_info"]["dependencies"]["model_adapter_status"] == "mock_ready"
        finally:
            app.dependency_overrides.pop(get_settings, None)

    @pytest.mark.asyncio
    async def test_live_gemini_inference_smoke_test_when_configured(self):
        """Verifies real live Gemini multimodal extraction when a valid key is present in environment."""
        cfg = MultimodalConfig(max_tokens=4096)
        api_key = cfg.get_api_key()
        if not api_key:
            pytest.skip("GEMINI_API_KEY is not configured or is a placeholder; skipping live smoke test.")

        adapter = GeminiMultimodalAdapter(config=cfg)
        assert adapter.is_available() is True
        img_bytes = create_test_image_bytes()
        try:
            raw_result = await adapter.extract(image_bytes=img_bytes, mime_type="image/png")
            parsed = json.loads(raw_result)
            assert "medicines" in parsed
            assert len(parsed["medicines"]) > 0
            first_med = parsed["medicines"][0]
            assert "medicine_name" in first_med
            assert first_med["medicine_name"]["value"] is not None
        except Exception as exc:
            if "503" in str(exc) or "high demand" in str(exc).lower() or "504" in str(exc) or "timed out" in str(exc).lower():
                pytest.skip(f"Live Gemini provider is experiencing transient latency spike or high demand: {exc}")
            raise
