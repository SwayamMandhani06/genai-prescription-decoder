"""
Pytest Fixtures for AURA-Rx Backend Testing
"""

import os
import shutil
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import get_settings


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
