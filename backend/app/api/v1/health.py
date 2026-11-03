"""
Health Check and Service Diagnostics API Route
Verifies service uptime, pipeline mode, RAG reference index availability,
storage writability, and active configuration readiness for container orchestration.
"""

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends
from ...config import Settings, get_settings
from ...schemas.health import HealthResponse
from ...multimodal.config import MultimodalConfig

router = APIRouter(prefix="", tags=["Health & Diagnostics"])
START_TIME = time.time()


def check_rag_reference_availability() -> tuple[bool, int, str]:
    """Verifies that authoritative CDSCO and RxNorm formulary reference datasets are present on disk."""
    possible_roots = [
        Path("data/reference"),
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "reference",
    ]
    ref_dir = None
    for r in possible_roots:
        if r.exists() and r.is_dir():
            ref_dir = r
            break

    if not ref_dir:
        return False, 0, "reference_directory_missing"

    cdsco_path = ref_dir / "cdsco_approved_drugs.json"
    if not cdsco_path.exists() or not cdsco_path.is_file():
        return False, 0, "cdsco_dataset_missing"

    try:
        with open(cdsco_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            count = len(data) if isinstance(data, list) else len(data.get("drugs", []))
            return True, count, "available"
    except Exception as exc:
        return False, 0, f"cdsco_parse_error: {str(exc)}"


def check_storage_writability(upload_dir: Path) -> tuple[bool, str]:
    """Tests filesystem writability by touching and removing an ephemeral canary file."""
    try:
        upload_dir.mkdir(parents=True, exist_ok=True)
        canary = upload_dir / f".health_canary_{uuid.uuid4().hex[:8]}.tmp"
        canary.write_text("health_check_ok", encoding="utf-8")
        canary.unlink(missing_ok=True)
        return True, "writable"
    except Exception as exc:
        return False, f"storage_error: {str(exc)}"


def check_config_readiness(settings: Settings) -> tuple[bool, list[str]]:
    """Validates runtime configuration parameter integrity."""
    issues = []
    if settings.MAX_UPLOAD_SIZE_BYTES <= 0:
        issues.append("MAX_UPLOAD_SIZE_BYTES must be positive")
    if settings.RETENTION_TTL_SECONDS < 0:
        issues.append("RETENTION_TTL_SECONDS cannot be negative")
    env_str = (settings.ENV or "").lower().strip()
    if env_str == "production" and settings.USE_MOCK_PIPELINE:
        issues.append("USE_MOCK_PIPELINE cannot be true in production")
    return len(issues) == 0, issues


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Returns service uptime, version, RAG index readiness, storage writability, and configuration diagnostics.",
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

    # 1. RAG Reference Index Diagnostics
    rag_ok, rag_count, rag_detail = check_rag_reference_availability()

    # 2. Storage Writability Diagnostics
    upload_dir = settings.ensure_upload_dir_exists()
    storage_ok, storage_detail = check_storage_writability(upload_dir)

    # 3. Active Configuration Readiness Diagnostics
    config_ok, config_issues = check_config_readiness(settings)

    if is_live_pipeline:
        if has_gemini_key and rag_ok and storage_ok and config_ok:
            overall_status = "healthy"
            adapter_status = "ready_configured"
        else:
            overall_status = "degraded"
            adapter_status = "missing_or_invalid_api_key" if not has_gemini_key else "dependency_degraded"
    else:
        if rag_ok and storage_ok and config_ok:
            overall_status = "healthy"
            adapter_status = "mock_ready"
        else:
            overall_status = "degraded"
            adapter_status = "mock_degraded"

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
                "rag_formulary_status": "ready" if rag_ok else "degraded",
                "rag_reference_records": rag_count,
                "rag_detail": rag_detail,
                "storage_service_status": "ready" if storage_ok else "unwritable",
                "storage_writability": storage_detail,
                "active_configuration_readiness": "ready" if config_ok else "invalid",
                "configuration_issues": config_issues,
                "retention_ttl_seconds": settings.RETENTION_TTL_SECONDS,
                "zero_retention_enforced": settings.RETENTION_TTL_SECONDS == 0,
                "lasa_service_status": "ready",
                "explanation_service_status": "ready",
            },
        },
    )
