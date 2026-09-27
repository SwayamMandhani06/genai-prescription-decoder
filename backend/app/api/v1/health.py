"""
Health Check and Service Diagnostics API Route
"""

import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from ...config import Settings, get_settings
from ...schemas.health import HealthResponse

router = APIRouter(prefix="", tags=["Health & Diagnostics"])
START_TIME = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Returns current service status, uptime, version, and pipeline execution mode.",
)
async def check_health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    uptime = time.time() - START_TIME
    now_iso = datetime.now(timezone.utc).isoformat()
    return HealthResponse(
        status="healthy",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        timestamp=now_iso,
        mock_mode=settings.USE_MOCK_PIPELINE,
        uptime_seconds=round(uptime, 2),
        system_info={
            "api_prefix": settings.API_V1_PREFIX,
            "max_upload_size_mb": settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024),
            "allowed_mime_types": settings.ALLOWED_IMAGE_TYPES,
        },
    )
