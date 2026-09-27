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
def sample_prescription_image():
    """Returns dummy PNG image bytes representing a prescription scan."""
    # Minimal valid 1x1 PNG bytes
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00"
        b"\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
    )
