"""
Health and Diagnostic Schemas for AURA-Rx Backend
"""

from typing import Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field("healthy", description="Current service health status")
    service: str = Field(..., description="Service identification name")
    version: str = Field(..., description="Semantic version string")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    mock_mode: bool = Field(True, description="Indicates if mock pipeline is currently active")
    uptime_seconds: float = Field(..., description="Uptime in seconds since server start")
    system_info: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic environment details")
