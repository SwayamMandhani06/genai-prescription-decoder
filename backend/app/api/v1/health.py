"""
Health Check and Service Diagnostics API Route
"""

import os
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
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or settings.GEMINI_API_KEY
    has_gemini_key = bool(gemini_key and len(gemini_key.strip()) > 5)

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
            "pipeline_mode": "mock" if settings.USE_MOCK_PIPELINE else "multimodal",
            "dependencies": {
                "multimodal_model_provider": "gemini" if not settings.USE_MOCK_PIPELINE else "mock",
                "gemini_api_key_configured": has_gemini_key,
                "rag_formulary_status": "ready",
                "lasa_service_status": "ready",
                "explanation_service_status": "ready",
                "storage_service_status": "ready",
            },
        },
    )
