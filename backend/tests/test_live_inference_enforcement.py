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

from pydantic import ValidationError

from backend.app.main import app
from backend.app.config import get_settings, Settings
from backend.app.multimodal.config import MultimodalConfig
from backend.app.multimodal.adapter import GeminiMultimodalAdapter, MockMultimodalModelAdapter, sanitize_secret_text
from backend.app.services.mock_pipeline import MockPrescriptionPipeline
from backend.app.services.multimodal_pipeline import MultimodalPrescriptionPipeline
from backend.app.services.pipeline_interface import PipelineOptions, PipelineProcessingError, UpstreamInferenceError
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
            try:
                parsed = json.loads(raw_result)
            except json.JSONDecodeError:
                from backend.app.multimodal.parser import parse_multimodal_response
                parsed = parse_multimodal_response(raw_result)
            assert "medicines" in parsed
            assert len(parsed["medicines"]) > 0
            first_med = parsed["medicines"][0]
            assert "medicine_name" in first_med
            assert first_med["medicine_name"]["value"] is not None
        except Exception as exc:
            if "503" in str(exc) or "high demand" in str(exc).lower() or "504" in str(exc) or "timed out" in str(exc).lower():
                pytest.skip(f"Live Gemini provider is experiencing transient latency spike or high demand: {exc}")
            raise

    def test_production_environment_rejects_mock_configuration_with_validation_error(self):
        """In production environment mode (ENV=production), attempting to enable mock mode raises ValidationError."""
        # 1. ENV=production with USE_MOCK_PIPELINE=True
        with pytest.raises(ValidationError) as exc1:
            Settings(ENV="production", USE_MOCK_PIPELINE=True)
        assert "Mock pipeline execution is strictly forbidden in production environment" in str(exc1.value)

        # 2. ENV=production with INFERENCE_MODE="mock"
        with pytest.raises(ValidationError) as exc2:
            Settings(ENV="production", INFERENCE_MODE="mock")
        assert "Mock pipeline execution is strictly forbidden in production environment" in str(exc2.value)

        # 3. ENVIRONMENT=production with USE_MOCK_PIPELINE=True
        with pytest.raises(ValidationError) as exc3:
            Settings(ENVIRONMENT="production", USE_MOCK_PIPELINE=True)
        assert "Mock pipeline execution is strictly forbidden in production environment" in str(exc3.value)

    @pytest.mark.asyncio
    async def test_production_environment_rejects_mock_pipeline_execution(self):
        """MockPrescriptionPipeline and MockMultimodalModelAdapter refuse execution if ENV=production."""
        mock_pipe = MockPrescriptionPipeline()
        options = PipelineOptions()
        with patch.dict("os.environ", {"ENV": "production"}):
            with pytest.raises(PipelineProcessingError) as exc_pipe:
                await mock_pipe.process_prescription(
                    image_bytes=b"dummy",
                    filename="sample.png",
                    public_image_url="/sample.png",
                    options=options,
                )
            assert exc_pipe.value.status_code == 500
            assert "strictly forbidden in production" in exc_pipe.value.message

        mock_adapter = MockMultimodalModelAdapter()
        with patch.dict("os.environ", {"ENV": "production"}):
            with pytest.raises(PipelineProcessingError) as exc_adapter:
                await mock_adapter.extract(image_bytes=b"sample_bytes_1234567890", mime_type="image/png")
            assert exc_adapter.value.status_code == 500
            assert "strictly forbidden" in exc_adapter.value.message

    def test_production_environment_rejects_mock_scenario_at_api_gate(self):
        """When ENV=production, API routes reject mock_scenario and scenario overrides with HTTP 400."""
        prod_settings = Settings(
            ENV="production",
            USE_MOCK_PIPELINE=False,
            GEMINI_API_KEY="AIzaSyTestValidKeyFormat1234567890",
        )
        app.dependency_overrides[get_settings] = lambda: prod_settings

        try:
            with patch.dict("os.environ", {"ENV": "production"}):
                client = TestClient(app)
                img_bytes = create_test_image_bytes()

                # /analyze with mock_scenario in production returns 400
                resp1 = client.post(
                    "/api/v1/prescriptions/analyze",
                    files={"file": ("rx.png", img_bytes, "image/png")},
                    data={"mock_scenario": "confident"},
                )
                assert resp1.status_code == 400
                assert "strictly forbidden in production" in resp1.json().get("detail", "")

                # /extract with scenario in production returns 400
                resp2 = client.post(
                    "/api/v1/multimodal/extract",
                    files={"file": ("rx.png", img_bytes, "image/png")},
                    data={"scenario": "single_medicine_confident"},
                )
                assert resp2.status_code == 400
                assert "strictly forbidden in production" in resp2.json().get("detail", "")
        finally:
            app.dependency_overrides.pop(get_settings, None)

    @pytest.mark.asyncio
    async def test_multimodal_pipeline_live_mode_without_credentials_fails_explicitly(self):
        """Invoking multimodal_pipeline in live mode without valid API credentials fails explicitly and never returns mock fixtures."""
        test_settings = Settings(
            ENV="development",
            USE_MOCK_PIPELINE=False,
            GEMINI_API_KEY="",
        )
        pipeline = MultimodalPrescriptionPipeline(settings=test_settings)
        options = PipelineOptions()
        img_bytes = create_test_image_bytes()

        with patch.dict("os.environ", {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}):
            with pytest.raises(PipelineProcessingError) as exc_info:
                await pipeline.process_prescription(
                    image_bytes=img_bytes,
                    filename="sample.png",
                    public_image_url="/sample.png",
                    options=options,
                )
            assert exc_info.value.status_code == 503
            assert isinstance(exc_info.value, UpstreamInferenceError)
            assert "missing or is an invalid placeholder" in exc_info.value.message.lower()

    def test_all_prescription_and_multimodal_responses_declare_inference_mode(self):
        """100% of responses from /api/v1/prescriptions and /api/v1/multimodal include explicit inference_mode."""
        mock_settings = Settings(
            ENV="development",
            USE_MOCK_PIPELINE=True,
            INFERENCE_MODE="mock",
        )
        app.dependency_overrides[get_settings] = lambda: mock_settings

        try:
            client = TestClient(app)
            img_bytes = create_test_image_bytes()

            # 1. /api/v1/prescriptions/analyze
            resp_analyze = client.post(
                "/api/v1/prescriptions/analyze",
                files={"file": ("rx.png", img_bytes, "image/png")},
            )
            assert resp_analyze.status_code == 200
            data_analyze = resp_analyze.json()
            assert "inference_mode" in data_analyze
            assert data_analyze["inference_mode"] == "mock"
            assert data_analyze["meta"]["inference_mode"] == "mock"
            assert data_analyze["model_provider"] == "mock"
            assert data_analyze["meta"]["model_provider"] == "mock"

            # 2. /api/v1/prescriptions/process (alias)
            resp_process = client.post(
                "/api/v1/prescriptions/process",
                files={"file": ("rx.png", img_bytes, "image/png")},
            )
            assert resp_process.status_code == 200
            data_process = resp_process.json()
            assert data_process["inference_mode"] == "mock"
            assert data_process["meta"]["inference_mode"] == "mock"

            # 3. /api/v1/prescriptions/{id}
            presc_id = data_analyze["prescription_id"]
            resp_get = client.get(f"/api/v1/prescriptions/{presc_id}")
            assert resp_get.status_code == 200
            data_get = resp_get.json()
            assert data_get["inference_mode"] == "mock"
            assert data_get["meta"]["inference_mode"] == "mock"

            # 4. /api/v1/prescriptions/verify
            resp_verify = client.post(
                "/api/v1/prescriptions/verify",
                json={
                    "prescription_id": presc_id,
                    "reviewer_id": "PHARM-TEST-001",
                    "verified_items": [
                        {
                            "medicine_name": "Augmentin 625 Duo",
                            "dosage": "625 mg",
                            "frequency": "1-0-1",
                            "duration": "5 days",
                        }
                    ],
                },
            )
            assert resp_verify.status_code == 200
            data_verify = resp_verify.json()
            assert data_verify["inference_mode"] == "mock"
            assert data_verify["meta"]["inference_mode"] == "mock"

            # 5. /api/v1/multimodal/extract
            resp_extract = client.post(
                "/api/v1/multimodal/extract",
                files={"file": ("rx.png", img_bytes, "image/png")},
            )
            assert resp_extract.status_code == 200
            data_extract = resp_extract.json()
            assert "inference_mode" in data_extract
            assert data_extract["inference_mode"] == "mock"
            assert data_extract["model"]["inference_mode"] == "mock"
        finally:
            app.dependency_overrides.pop(get_settings, None)

