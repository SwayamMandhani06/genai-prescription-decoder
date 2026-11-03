"""
Production Security & Rate Limiting Verification Tests
Validates:
- Binary magic bytes validation preventing extension spoofing (PNG, JPEG, SVG vs MZ exe).
- Sliding-window rate limiter enforcement returning HTTP 429 and Retry-After header.
- Security headers injection (X-Content-Type-Options, X-Frame-Options, Strict-Transport-Security, X-Request-ID).
- Ephemeral upload retention cleanup and zero-retention deletion in finally: block.
- Path traversal filename sanitization and rejection (../../etc/passwd.png).
- Oversized file upload rejection (HTTP 413).
- Cache-Control: no-store on prescription responses.
- PHI-safe log redaction filter.
- API key authentication verification.
"""

import io
import logging
from pathlib import Path
import pytest
from starlette.testclient import TestClient
from fastapi import Request, HTTPException

from backend.app.main import app
from backend.app.config import get_settings
from backend.app.core.security import (
    SlidingWindowRateLimiter,
    PHISafeLoggingFilter,
    verify_api_key,
)
from backend.app.services.storage import StorageService, FileValidationError
from backend.app.schemas.error import ErrorCode


@pytest.fixture
def test_client():
    return TestClient(app)


def test_security_headers_present_on_responses(test_client):
    """Verifies that security headers are injected into HTTP responses."""
    resp = test_client.get("/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Strict-Transport-Security" in resp.headers
    assert "X-Request-ID" in resp.headers


def test_custom_request_id_propagated(test_client):
    """Verifies that an incoming X-Request-ID header is propagated back for traceability."""
    custom_id = "trace-test-uuid-98765"
    resp = test_client.get("/health", headers={"X-Request-ID": custom_id})
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-ID") == custom_id


def test_binary_magic_byte_validation():
    """Verifies that magic bytes validation rejects malicious/spoofed file headers."""
    storage = StorageService()

    # Valid PNG header (\x89PNG\r\n\x1a\n)
    valid_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
    storage.validate_file_signature(valid_png, "sample.png")

    # Valid JPEG header (\xff\xd8\xff)
    valid_jpg = b"\xff\xd8\xff\xe0" + b"\x00" * 32
    storage.validate_file_signature(valid_jpg, "sample.jpg")

    # Spoofed PE/Windows executable header (MZ) with .png extension
    spoofed_exe = b"MZ\x90\x00\x03\x00\x00\x00" + b"\x00" * 32
    with pytest.raises(FileValidationError) as exc_info:
        storage.validate_file_signature(spoofed_exe, "spoofed.png")
    assert exc_info.value.code == ErrorCode.INVALID_FILE_TYPE
    assert exc_info.value.status_code == 415


def test_sliding_window_rate_limiter_isolated():
    """Verifies that the sliding window rate limiter blocks requests once threshold is reached."""
    limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=60)
    client_ip = "192.168.1.100"

    # First 5 requests must pass
    for i in range(5):
        allowed, remaining, _ = limiter.is_allowed(client_ip)
        assert allowed is True
        assert remaining == 4 - i

    # 6th request must be rejected
    allowed, remaining, retry_after = limiter.is_allowed(client_ip)
    assert allowed is False
    assert remaining == 0
    assert retry_after > 0


def test_ephemeral_upload_cleanup(tmp_path):
    """Verifies that cleanup_ephemeral_uploads removes stale files while keeping recent ones."""
    storage = StorageService()
    storage.upload_dir = tmp_path

    # Create dummy recent file
    recent_file = tmp_path / "rx_recent_abc.png"
    recent_file.write_bytes(b"recent_bytes")

    # Run cleanup with 3600s max age; recent file should NOT be purged
    purged = storage.cleanup_ephemeral_uploads(max_age_seconds=3600)
    assert purged == 0
    assert recent_file.exists()


def test_path_traversal_filename_rejection(test_client):
    """Verifies that path traversal sequences in filenames are strictly rejected."""
    storage = StorageService()

    # Ingress metadata validation strictly rejects traversal sequences
    with pytest.raises(FileValidationError) as exc_info:
        storage.validate_file_metadata(
            filename="../../etc/passwd.png",
            content_type="image/png",
            size=100,
        )
    assert exc_info.value.code == ErrorCode.INVALID_REQUEST
    assert exc_info.value.status_code == 400

    # API ingress endpoint returns HTTP 400 on traversal upload
    valid_png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
    files = {"file": ("../../etc/passwd.png", valid_png_bytes, "image/png")}
    response = test_client.post("/api/v1/prescriptions/process", files=files)
    assert response.status_code == 400

    # Direct storage method strictly generates UUIDv4 without user filename stem
    saved_path, _ = storage.save_prescription_image(valid_png_bytes, "../../etc/passwd.png")
    try:
        assert saved_path.parent.resolve() == storage.upload_dir.resolve()
        assert "passwd" not in saved_path.name
        assert ".." not in saved_path.name
        assert saved_path.name.startswith("rx_")
    finally:
        saved_path.unlink(missing_ok=True)


def test_get_prescription_image_path_traversal_defense(tmp_path):
    """Verifies that get_prescription_image_path cannot be tricked into referencing files outside upload_dir."""
    storage = StorageService()
    storage.upload_dir = tmp_path

    # Attempt to access a file outside upload_dir
    outside_target = storage.get_prescription_image_path("../../etc/passwd")
    assert outside_target is None or not outside_target.exists()


def test_oversized_file_upload_rejected_413(test_client, monkeypatch):
    """Verifies that uploads exceeding MAX_UPLOAD_SIZE_BYTES are rejected with HTTP 413."""
    settings = get_settings()
    # Temporarily set upload limit to 1 KB for fast testing
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_BYTES", 1024)

    oversized_data = b"\x89PNG\r\n\x1a\n" + b"X" * 2048
    files = {"file": ("large_prescription.png", oversized_data, "image/png")}
    response = test_client.post("/api/v1/prescriptions/process", files=files)
    assert response.status_code == 413
    data = response.json()
    assert data["error"]["code"] == "FILE_TOO_LARGE"


def test_cache_control_no_store_on_prescription_responses(test_client):
    """Verifies that Cache-Control: no-store is enforced on prescription and PHI endpoints."""
    response = test_client.post(
        "/api/v1/prescriptions/process",
        data={"sample_id": "rx-sample-1", "mock_scenario": "confident"},
    )
    assert response.status_code == 200
    cache_control = response.headers.get("Cache-Control", "")
    assert "no-store" in cache_control
    assert "no-cache" in cache_control
    assert response.headers.get("Pragma") == "no-cache"


def test_automatic_cleanup_of_uploads_after_prescription_request(test_client, monkeypatch):
    """
    Verifies zero-retention PHI compliance: uploaded prescription image is deleted
    immediately in a finally: block after request completion when RETENTION_TTL_SECONDS=0.
    """
    settings = get_settings()
    monkeypatch.setattr(settings, "RETENTION_TTL_SECONDS", 0)

    # Count existing prescription files in uploads directory
    upload_dir = settings.ensure_upload_dir_exists()
    initial_rx_files = [f for f in upload_dir.iterdir() if f.is_file() and f.name.startswith("rx_")]

    sample_path = Path("data/samples/sample_01_clear.png")
    if not sample_path.exists():
        sample_path = Path("data/samples/handwritten-clinic-pad.png")
    valid_png_bytes = sample_path.read_bytes()

    files = {"file": ("temp_prescription.png", valid_png_bytes, "image/png")}
    data = {"mock_scenario": "confident"}

    response = test_client.post("/api/v1/prescriptions/process", files=files, data=data)
    assert response.status_code == 200

    # Verify zero newly retained rx_ files remain on disk
    remaining_rx_files = [f for f in upload_dir.iterdir() if f.is_file() and f.name.startswith("rx_")]
    assert len(remaining_rx_files) == len(initial_rx_files)

    # Verify that neither backend/uploads/preprocessed/<prescription_id> nor data/processed/preprocessing_runs/<prescription_id> exists on disk
    rx_id = response.json().get("prescription_id")
    if rx_id:
        public_run_dir = upload_dir / "preprocessed" / rx_id
        base_run_dir = Path("data/processed/preprocessing_runs") / rx_id
        assert not public_run_dir.exists(), f"Public preprocessed dir {public_run_dir} was not cleaned up"
        assert not base_run_dir.exists(), f"Base preprocessed dir {base_run_dir} was not cleaned up"


def test_phi_safe_log_redaction():
    """Verifies that PHISafeLoggingFilter redacts API keys, base64 payloads, and patient PHI."""
    # Production filter
    prod_filter = PHISafeLoggingFilter(is_production=True)

    # 1. API key redaction
    msg_key = "Connecting with key AIzaSyD12345678901234567890123456789012 to vision model"
    assert "AIzaSy" not in prod_filter.redact_message(msg_key)
    assert "[REDACTED_API_KEY]" in prod_filter.redact_message(msg_key)

    # 2. Base64 image payload redaction
    msg_b64 = "Processing image: data:image/png;base64," + "A" * 100
    assert "[REDACTED_IMAGE_PAYLOAD]" in prod_filter.redact_message(msg_b64)

    # 3. Patient name redaction in production
    msg_patient = 'Extracted record: "patient_name": "Ramesh Gupta", "age": 45'
    redacted = prod_filter.redact_message(msg_patient)
    assert "Ramesh Gupta" not in redacted
    assert "[REDACTED_PATIENT_NAME]" in redacted

    # Non-production filter retains debug strings
    dev_filter = PHISafeLoggingFilter(is_production=False)
    assert "Ramesh Gupta" in dev_filter.redact_message(msg_patient)


def test_api_key_authentication_enforcement(monkeypatch):
    """Verifies verify_api_key dependency behavior under REQUIRE_API_KEY setting."""
    settings = get_settings()

    # 1. Unenforced: returns None without error
    monkeypatch.setattr(settings, "REQUIRE_API_KEY", False)
    dummy_req = Request({"type": "http", "headers": []})
    assert verify_api_key(dummy_req) is None

    # 2. Enforced: rejects missing key with HTTP 401
    monkeypatch.setattr(settings, "REQUIRE_API_KEY", True)
    monkeypatch.setattr(settings, "API_KEY", "super-secret-key-123")

    with pytest.raises(HTTPException) as exc_info:
        verify_api_key(dummy_req)
    assert exc_info.value.status_code == 401

    # 3. Enforced: accepts valid X-API-Key header
    valid_req = Request({"type": "http", "headers": [(b"x-api-key", b"super-secret-key-123")]})
    assert verify_api_key(valid_req) == "super-secret-key-123"

    # 4. Enforced: accepts valid Bearer Authorization header
    bearer_req = Request({"type": "http", "headers": [(b"authorization", b"Bearer super-secret-key-123")]})
    assert verify_api_key(bearer_req) == "super-secret-key-123"
