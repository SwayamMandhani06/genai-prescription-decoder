"""
API Router Aggregator for AURA-Rx Backend
Aggregates versioned routes under /api/v1
"""

from fastapi import APIRouter
from .v1.health import router as health_router
from .v1.prescriptions import router as prescriptions_router
from .v1.ocr import router as ocr_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(prescriptions_router)
api_v1_router.include_router(ocr_router)
