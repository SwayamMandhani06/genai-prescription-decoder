"""
API Router Aggregator for AURA-Rx Backend
Aggregates versioned routes under /api/v1
"""

from fastapi import APIRouter
from .v1.health import router as health_router
from .v1.prescriptions import router as prescriptions_router
from .v1.ocr import router as ocr_router
from .v1.multimodal import router as multimodal_router
from .v1.validation import router as validation_router
from .v1.confidence import router as confidence_router
from .v1.abstention import abstention_router, verification_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(prescriptions_router)
api_v1_router.include_router(ocr_router)
api_v1_router.include_router(multimodal_router)
api_v1_router.include_router(validation_router)
api_v1_router.include_router(confidence_router)
api_v1_router.include_router(abstention_router)
api_v1_router.include_router(verification_router)



