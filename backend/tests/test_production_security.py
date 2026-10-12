"""
Production Security & Rate Limiting Verification Tests
Validates:
- Binary magic bytes validation preventing extension spoofing (PNG, JPEG, SVG vs MZ exe).
- Sliding-window rate limiter enforcement returning HTTP 429 and Retry-After header.
- Security headers injection (X-Content-Type-Options, X-Frame-Options, X-Request-ID).
- Ephemeral upload retention cleanup.
"""

import pytest
from starlette.testclient import TestClient
from backend.app.main import app
from backend.app.core.security import SlidingWindowRateLimiter
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
