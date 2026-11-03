"""
DawaAI FastAPI Main Application
Explainable Multimodal AI for Handwritten Prescription Understanding
"""

import logging
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError

from .config import Settings, get_settings
from .api.router import api_v1_router
from .schemas.error import ErrorCode, ErrorDetail, ErrorResponse
from .schemas.health import HealthResponse
from .services.pipeline_interface import PipelineProcessingError

from .core.security import PHISafeLoggingFilter

# Configure application logging with PHI-safe redaction filter
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("dawaai")
_settings = get_settings()
_is_prod = (_settings.ENV or "").lower().strip() == "production"
_phi_filter = PHISafeLoggingFilter(is_production=_is_prod)
logging.getLogger().addFilter(_phi_filter)
logger.addFilter(_phi_filter)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.ensure_upload_dir_exists()
    logger.info("DawaAI FastAPI Backend started on %s:%s (Mock Mode: %s)", settings.HOST, settings.PORT, settings.USE_MOCK_PIPELINE)
    yield
    logger.info("DawaAI FastAPI Backend shutting down.")


def create_app() -> FastAPI:
    settings = get_settings()
    env_str = (settings.ENV or "").lower().strip()
    is_prod = env_str == "production"

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=(
            "Assistive, evidence-grounded prescription decoding API. "
            "Combines multimodal handwriting transcription, CDSCO & RxNorm formulary grounding, "
            "ISMP Tall Man LASA screening, and vernacular posology translation."
        ),
        lifespan=lifespan,
    )

    # --------------------------------------------------------------------------
    # 1. CORS Middleware (Strict allowlist in production, no wildcard with credentials)
    # --------------------------------------------------------------------------
    cors_origins = list(settings.CORS_ORIGINS) if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
    if is_prod:
        cors_origins = [orig for orig in cors_origins if orig.strip() != "*"]
        if not cors_origins:
            cors_origins = ["https://dawaai-prescription-decoder.vercel.app"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_origin_regex=r"^https://.*\.vercel\.app$" if is_prod else r"^(https://.*\.vercel\.app|http://(localhost|127\.0\.0\.1):(517\d|3000|800\d))$",
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
    # 2. Security & Request Correlation Headers Middleware
    # --------------------------------------------------------------------------
    @app.middleware("http")
    async def security_and_tracing_middleware(request: Request, call_next):
        req_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = req_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Anti-caching headers for all patient health information endpoints
        path = request.url.path
        if "/prescriptions" in path or "/multimodal" in path or "/ocr" in path:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"

        return response

    # --------------------------------------------------------------------------
    # 2. Static File Serving for Uploaded Original Prescription Images
    # --------------------------------------------------------------------------
    upload_dir = settings.ensure_upload_dir_exists()
    app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

    # --------------------------------------------------------------------------
    # 3. Exception Handlers (Standardizing to PLAN.md Section 6 Error Contract)
    # --------------------------------------------------------------------------
    def _extract_request_id(request: Request) -> str:
        return getattr(request.state, "request_id", None) or request.headers.get("x-request-id") or str(uuid.uuid4())

    def _make_error_response(request: Request, status_code: int, error_response: ErrorResponse) -> JSONResponse:
        req_id = _extract_request_id(request)
        error_response.request_id = req_id
        headers = {
            "X-Request-ID": req_id,
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
        }
        path = request.url.path
        if "/prescriptions" in path or "/multimodal" in path or "/ocr" in path:
            headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            headers["Pragma"] = "no-cache"
        return JSONResponse(status_code=status_code, content=error_response.model_dump(), headers=headers)

    @app.exception_handler(PipelineProcessingError)
    async def pipeline_processing_error_handler(request: Request, exc: PipelineProcessingError):
        logger.warning("Pipeline processing error [%s]: %s (Stage: %s)", exc.code, exc.message, exc.stage)
        payload = ErrorResponse(
            error=ErrorDetail(
                code=exc.code,
                message=exc.message,
                stage=exc.stage,
                retryable=exc.retryable,
                details=exc.details,
            ),
            prescription_id=exc.prescription_id,
            original_image_url=exc.original_image_url,
        )
        return _make_error_response(request, exc.status_code, payload)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.info("Request validation failed on %s: %s", request.url.path, exc.errors())
        safe_errors = [
            {"loc": list(err.get("loc", [])), "msg": str(err.get("msg")), "type": str(err.get("type"))}
            for err in exc.errors()
        ]
        payload = ErrorResponse(
            error=ErrorDetail(
                code=ErrorCode.INVALID_REQUEST,
                message="Incoming request parameters or payload failed schema validation.",
                stage="api_ingress",
                retryable=False,
                details={"validation_errors": safe_errors},
            ),
            detail="Request validation failed.",
        )
        return _make_error_response(request, status.HTTP_422_UNPROCESSABLE_ENTITY, payload)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        # Map HTTP status codes to stable error codes
        code_map = {
            400: ErrorCode.INVALID_REQUEST,
            401: ErrorCode.INVALID_REQUEST,
            403: ErrorCode.INVALID_REQUEST,
            404: ErrorCode.INVALID_REQUEST,
            413: ErrorCode.FILE_TOO_LARGE,
            415: ErrorCode.INVALID_FILE_TYPE,
            422: ErrorCode.VALIDATION_FAILED,
            429: ErrorCode.RATE_LIMIT_EXCEEDED,
            500: ErrorCode.INTERNAL_ERROR,
            502: ErrorCode.MODEL_UNAVAILABLE,
            503: ErrorCode.MODEL_UNAVAILABLE,
            504: ErrorCode.MODEL_UNAVAILABLE,
        }
        err_code = code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
        msg = str(exc.detail) if exc.detail else "An HTTP error occurred."
        payload = ErrorResponse(
            error=ErrorDetail(
                code=err_code,
                message=msg,
                stage="api_routing",
                retryable=exc.status_code in (429, 500, 502, 503, 504),
                details={"status_code": exc.status_code},
            ),
            detail=msg,
        )
        return _make_error_response(request, exc.status_code, payload)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled server exception on %s: %s", request.url.path, str(exc), exc_info=True)
        payload = ErrorResponse(
            error=ErrorDetail(
                code=ErrorCode.INTERNAL_ERROR,
                message="An unexpected server error occurred while processing the prescription request.",
                stage="server_runtime",
                retryable=True,
                details={"path": request.url.path},
            ),
            detail="Internal Server Error",
        )
        return _make_error_response(request, status.HTTP_500_INTERNAL_SERVER_ERROR, payload)

    # --------------------------------------------------------------------------
    # 4. Route Mounting
    # --------------------------------------------------------------------------
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    # --------------------------------------------------------------------------
    # 5. Root Index & Service Info
    # --------------------------------------------------------------------------
    @app.get("/", tags=["Root"])
    async def root_index():
        return {
            "project": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "docs": "/docs",
            "redoc": "/redoc",
            "health": f"{settings.API_V1_PREFIX}/health",
            "root_health": "/health",
            "status": "operational",
        }

    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["Health & Diagnostics"],
        summary="Root Health Check",
        description="Alias for /api/v1/health providing standard container orchestrator health checks.",
    )
    async def root_health(settings: Settings = Depends(get_settings)) -> HealthResponse:
        from .api.v1.health import check_health
        return await check_health(settings=settings)

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return app


app = create_app()
