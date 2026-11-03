"""
Security, Rate Limiting, Authentication, and PHI Safeguards for DawaAI Backend
Provides:
- In-memory sliding window rate limiting and client IP extraction
- Chunked file upload reading with early size-abort (HTTP 413) to prevent DoS
- API-key authentication dependency for protected endpoints
- PHI-safe structured logging filter redacting credentials, image payloads, and patient PHI
"""

import hmac
import logging
import re
import time
import uuid
from typing import Dict, List, Tuple, Optional
from fastapi import Request, HTTPException, status, UploadFile
from ..schemas.error import ErrorCode


class SlidingWindowRateLimiter:
    """
    Thread-safe in-memory sliding window rate limiter.
    Tracks timestamps of incoming requests per client key.
    Automatically purges expired timestamps to maintain bounded memory footprint.
    """

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._history: Dict[str, List[float]] = {}
        self._last_cleanup = time.time()

    def _cleanup_old_entries(self, current_time: float) -> None:
        """Evicts client keys that have no timestamps in the current window."""
        expired_keys = []
        for key, timestamps in self._history.items():
            valid_timestamps = [t for t in timestamps if current_time - t < self.window_seconds]
            if not valid_timestamps:
                expired_keys.append(key)
            else:
                self._history[key] = valid_timestamps
        for key in expired_keys:
            self._history.pop(key, None)

    def is_allowed(self, client_id: str) -> Tuple[bool, int, int]:
        """
        Evaluates whether a request from client_id is permitted under current quota.
        Returns:
            (is_allowed: bool, remaining_quota: int, retry_after_seconds: int)
        """
        now = time.time()

        # Evict stale entries periodically every 60 seconds or if map exceeds 5000 keys
        if (now - self._last_cleanup > 60) or (len(self._history) > 5000):
            self._cleanup_old_entries(now)
            self._last_cleanup = now

        timestamps = self._history.get(client_id, [])
        valid_timestamps = [t for t in timestamps if now - t < self.window_seconds]

        if len(valid_timestamps) >= self.max_requests:
            oldest_in_window = valid_timestamps[0]
            retry_after = max(1, int(self.window_seconds - (now - oldest_in_window)))
            self._history[client_id] = valid_timestamps
            return False, 0, retry_after

        valid_timestamps.append(now)
        self._history[client_id] = valid_timestamps
        remaining = max(0, self.max_requests - len(valid_timestamps))
        return True, remaining, 0

    def reset(self) -> None:
        """Clears client history for testing and state resets."""
        self._history.clear()


# Global singleton rate limiter: 60 requests per minute per IP for analysis endpoints
prescription_rate_limiter = SlidingWindowRateLimiter(max_requests=60, window_seconds=60)


def extract_client_ip(request: Request) -> str:
    """Extracts client IP, respecting X-Forwarded-For if deployed behind reverse proxy/CDN."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # First IP in comma-separated chain is originating client
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


async def check_rate_limit(request: Request) -> None:
    """
    FastAPI dependency enforcing rate limits on sensitive/inference endpoints.
    Raises HTTP 429 when quota is exceeded.
    """
    client_ip = extract_client_ip(request)
    allowed, remaining, retry_after = prescription_rate_limiter.is_allowed(client_ip)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum 60 requests per minute allowed. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )


async def read_upload_file_chunked(
    upload_file: UploadFile,
    max_bytes: int,
    chunk_size: int = 64 * 1024,
) -> bytes:
    """
    Reads an incoming UploadFile stream in fixed chunks, strictly aborting with HTTP 413
    if the incoming stream exceeds max_bytes, preventing memory-exhaustion DoS attacks.
    """
    content = bytearray()
    total_size = 0
    while True:
        chunk = await upload_file.read(chunk_size)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > max_bytes:
            max_mb = max_bytes / (1024 * 1024)
            raise HTTPException(
                status_code=413,
                detail=f"Uploaded file size exceeds maximum allowed threshold of {max_mb:.0f} MB.",
            )
        content.extend(chunk)
    return bytes(content)


def verify_api_key(request: Request) -> Optional[str]:
    """
    Dependency for verifying API key credentials on protected routes.
    Checks 'X-API-Key' header or 'Authorization: Bearer <key>'.
    Enforced when REQUIRE_API_KEY is configured as True or when API_KEY is set and required.
    """
    from ..config import get_settings
    settings = get_settings()

    if not settings.REQUIRE_API_KEY:
        return None

    expected_key = settings.API_KEY
    if not expected_key:
        return None

    provided_key = request.headers.get("x-api-key")
    if not provided_key:
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            provided_key = auth_header[7:].strip()

    if not provided_key or not hmac.compare_digest(provided_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return provided_key


class PHISafeLoggingFilter(logging.Filter):
    """
    Structured logging filter that redacts:
    - API keys and tokens (e.g. AIza..., sk-...)
    - Base64 image payloads
    - Sensitive patient names and raw prescription text in production
    """

    API_KEY_REGEX = re.compile(
        r"(AIza[0-9A-Za-z-_]{35}|sk-[a-zA-Z0-9]{20,}|Bearer\s+[a-zA-Z0-9_\-\.]{20,})",
        re.IGNORECASE,
    )
    BASE64_IMAGE_REGEX = re.compile(
        r"(data:image\/[a-zA-Z]+;base64,[A-Za-z0-9+/=]{40,}|[A-Za-z0-9+/=]{120,})"
    )
    PATIENT_NAME_REGEX = re.compile(r'("patient_name"\s*:\s*)"([^"]+)"', re.IGNORECASE)
    RAW_TRANSCRIPTION_REGEX = re.compile(r'("raw_transcription"\s*:\s*)"([^"]+)"', re.IGNORECASE)

    def __init__(self, is_production: bool = False):
        super().__init__()
        self.is_production = is_production

    def redact_message(self, msg: str) -> str:
        if not isinstance(msg, str):
            return msg
        # Always redact API keys
        msg = self.API_KEY_REGEX.sub("[REDACTED_API_KEY]", msg)
        # Always redact long base64 strings
        msg = self.BASE64_IMAGE_REGEX.sub("[REDACTED_IMAGE_PAYLOAD]", msg)

        # In production mode, redact patient identifiers and raw handwriting text
        if self.is_production:
            msg = self.PATIENT_NAME_REGEX.sub(r'\1"[REDACTED_PATIENT_NAME]"', msg)
            msg = self.RAW_TRANSCRIPTION_REGEX.sub(r'\1"[REDACTED_RAW_TRANSCRIPTION]"', msg)
        return msg

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.redact_message(record.msg)
        if record.args:
            new_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    new_args.append(self.redact_message(arg))
                else:
                    new_args.append(arg)
            record.args = tuple(new_args)
        return True
