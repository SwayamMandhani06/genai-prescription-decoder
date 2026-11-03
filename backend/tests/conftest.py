"""
Pytest Fixtures and Configuration for AURA-Rx / DawaAI Backend Testing
"""

import os
import shutil
import tempfile
import warnings
from pathlib import Path

# Silence harmless third-party deprecation warnings during testing
warnings.filterwarnings("ignore", message=".*httpx.*")
warnings.filterwarnings("ignore", category=DeprecationWarning)

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import get_settings


def pytest_configure(config):
    """Registers custom markers for test suite segregation."""
    config.addinivalue_line(
        "markers", "unit: fast, deterministic unit and integration tests using dependency injection or fixtures"
    )
    config.addinivalue_line(
        "markers", "live_inference: end-to-end tests requiring live VLM/OCR execution on data/samples/"
    )
    config.addinivalue_line(
        "markers", "integration: integration tests between multi-stage pipeline components"
    )


def pytest_collection_modifyitems(config, items):
    """
    Categorizes tests into `unit` vs `live_inference` if not already explicitly tagged:
    - Tests with marker `live_inference` require physical sample images or live model inference.
    - All other tests default to `unit` for fast, reproducible CI execution.
    """
    for item in items:
        # If test is explicitly marked with live_inference, respect it
        if "live_inference" in item.keywords:
            continue
        # If item has no marker or is in unit test files, ensure unit marker is attached
        if "unit" not in item.keywords:
            item.add_marker(pytest.mark.unit)


@pytest.fixture(scope="session", autouse=True)
def configure_test_environment():
    """Ensures automated unit tests default to mock mode to prevent unexpected API costs and ensure reproducibility."""
    settings = get_settings()
    original_mock = settings.USE_MOCK_PIPELINE
    settings.USE_MOCK_PIPELINE = True
    yield
    settings.USE_MOCK_PIPELINE = original_mock


@pytest.fixture(scope="session")
def client():
    """Returns a TestClient instance for API integration testing."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def temp_upload_dir():
    """Provides an isolated temporary upload directory for test isolation."""
    temp_dir = Path(tempfile.mkdtemp(prefix="aura_test_uploads_"))
    settings = get_settings()
    original_upload_dir = settings.UPLOAD_DIR
    settings.UPLOAD_DIR = temp_dir
    yield temp_dir
    # Cleanup after test session
    settings.UPLOAD_DIR = original_upload_dir
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_prescription_image() -> bytes:
    """Returns valid PNG image bytes representing a readable clinical prescription scan."""
    import io
    from PIL import Image, ImageDraw

    im = Image.new("RGB", (400, 500), color=(250, 250, 250))
    draw = ImageDraw.Draw(im)
    draw.text((20, 20), "Rx Clinic Prescription Pad", fill=(20, 20, 20))
    draw.line([(20, 45), (380, 45)], fill=(60, 60, 60), width=2)
    draw.text((20, 70), "Augmentin 625 Duo - 1 tab BD x 5 days", fill=(10, 10, 80))
    draw.text((20, 100), "Dolo 650 - 1 tab TDS SOS", fill=(10, 10, 80))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def tiny_prescription_image() -> bytes:
    """Returns valid 1x1 PNG bytes for testing dimensional insufficiency rejection."""
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?"
        b"\x00\x05\xfe\x02\xfe\r\xefF\xb8\x00\x00\x00\x00IEND\xaeB`\x82"
    )


@pytest.fixture
def corrupted_image_bytes() -> bytes:
    """Returns truncated, non-decodable bytes for corruption testing."""
    return b"NOT_A_REAL_IMAGE_DATA_HEADER_CORRUPTED_STREAM"


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Resets the singleton prescription rate limiter before each test to prevent test runner quota exhaustion."""
    from backend.app.core.security import prescription_rate_limiter
    prescription_rate_limiter.reset()
