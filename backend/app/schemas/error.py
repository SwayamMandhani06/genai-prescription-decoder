"""
Stable Error and Failure Schemas
Implements the contract defined in Section 6 and Section 11 of PLAN.md.
"""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    """
    Standard machine-readable error codes specified in PLAN.md.
    """
    INVALID_REQUEST = "INVALID_REQUEST"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    IMAGE_QUALITY_INSUFFICIENT = "IMAGE_QUALITY_INSUFFICIENT"
    PROCESSING_FAILED = "PROCESSING_FAILED"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorDetail(BaseModel):
    """
    Detailed error payload safe for frontend display.
    Must never expose internal stack traces, GPU worker secrets, or unhandled exceptions.
    """
    code: ErrorCode = Field(..., description="Stable machine-readable error code")
    message: str = Field(..., description="Human-readable safe explanation for client display")
    stage: str = Field(..., description="The pipeline stage where the failure occurred")
    retryable: bool = Field(True, description="Indicates whether client retry is clinically/technically sensible")
    details: Dict[str, Any] = Field(default_factory=dict, description="Structured safe diagnostics")


class ErrorResponse(BaseModel):
    """
    Standard top-level error response envelope defined in PLAN.md Section 6.
    """
    error: ErrorDetail
    detail: Optional[str] = Field(None, description="FastAPI/OpenAPI compatibility field")
    prescription_id: Optional[str] = Field(None, description="Traceable prescription ID if assigned")
    original_image_url: Optional[str] = Field(None, description="Original image URL if preserved")

    def model_post_init(self, __context: Any) -> None:
        if self.detail is None:
            self.detail = self.error.message
