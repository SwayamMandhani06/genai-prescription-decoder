"""
Health Check and Service Diagnostics API Route
"""

import os
import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from ...config import Settings, get_settings
from ...schemas.health import HealthResponse

from ...multimodal.config import MultimodalConfig

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
    raw_key = (
        getattr(settings, "GEMINI_API_KEY", None)
        or getattr(settings, "GOOGLE_API_KEY", None)
    )
    if raw_key is None:
        raw_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    has_gemini_key = MultimodalConfig.is_valid_key(raw_key)

    is_live_pipeline = not settings.USE_MOCK_PIPELINE
    configured_model = (
        getattr(settings, "MULTIMODAL_MODEL_ID", None)
        or getattr(settings, "GEMINI_MODEL", None)
        or MultimodalConfig().model_id
    )

    if is_live_pipeline:
        if has_gemini_key:
            overall_status = "healthy"
            adapter_status = "ready_configured"
        else:
            overall_status = "degraded"
            adapter_status = "missing_or_invalid_api_key"
    else:
        overall_status = "healthy"
        adapter_status = "mock_ready"

    return HealthResponse(
        status=overall_status,
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
                "configured_model": configured_model,
                "gemini_api_key_configured": has_gemini_key,
                "model_adapter_status": adapter_status,
                "rag_formulary_status": "ready",
                "lasa_service_status": "ready",
                "explanation_service_status": "ready",
                "storage_service_status": "ready",
            },
        },
    )

