"""
DawaAI FastAPI Main Application
Explainable Multimodal AI for Handwritten Prescription Understanding
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError

from .config import Settings, get_settings
from .api.router import api_v1_router
from .schemas.error import ErrorCode, ErrorDetail, ErrorResponse
from .schemas.health import HealthResponse
from .services.pipeline_interface import PipelineProcessingError

# Configure application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("dawaai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.ensure_upload_dir_exists()
    logger.info("DawaAI FastAPI Backend started on %s:%s (Mock Mode: %s)", settings.HOST, settings.PORT, settings.USE_MOCK_PIPELINE)
    yield
    logger.info("DawaAI FastAPI Backend shutting down.")


def create_app() -> FastAPI:
    settings = get_settings()

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
    # 1. CORS Middleware
    # --------------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --------------------------------------------------------------------------
    # 2. Static File Serving for Uploaded Original Prescription Images
    # --------------------------------------------------------------------------
    upload_dir = settings.ensure_upload_dir_exists()
    app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

    # --------------------------------------------------------------------------
    # 3. Exception Handlers (Standardizing to PLAN.md Section 6 Error Contract)
    # --------------------------------------------------------------------------
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
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump())

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
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload.model_dump())

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        # Map HTTP status codes to stable error codes
        code_map = {
            400: ErrorCode.INVALID_REQUEST,
            404: ErrorCode.INVALID_REQUEST,
            413: ErrorCode.FILE_TOO_LARGE,
            415: ErrorCode.INVALID_FILE_TYPE,
            422: ErrorCode.VALIDATION_FAILED,
            500: ErrorCode.INTERNAL_ERROR,
            503: ErrorCode.MODEL_UNAVAILABLE,
            504: ErrorCode.INTERNAL_ERROR,
        }
        err_code = code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
        payload = ErrorResponse(
            error=ErrorDetail(
                code=err_code,
                message=str(exc.detail),
                stage="api_routing",
                retryable=exc.status_code in (500, 503, 504),
                details={"status_code": exc.status_code},
            ),
            detail=str(exc.detail),
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump())

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
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload.model_dump())

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

    return app


app = create_app()
