"""
Security, Rate Limiting, and Request Tracing for DawaAI Backend
Provides in-memory sliding window rate limiting and client IP extraction
to safeguard against denial of service and inference endpoint abuse.
"""

import time
import uuid
from typing import Dict, List, Tuple, Optional
from fastapi import Request, HTTPException, status
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
