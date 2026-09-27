"""
FastAPI Routes for Phase 8: Confidence Estimation & Calibration.
Endpoints:
- GET  /api/v1/confidence/config: Active confidence config and calibration status
- POST /api/v1/confidence/evaluate: Evaluate confidence for extraction / validation signals
- POST /api/v1/confidence/metrics: Calculate empirical ECE, MCE, Brier score, and bins
- GET  /api/v1/confidence/fixtures: Retrieve deterministic evaluation fixtures
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from ai.confidence.service import get_confidence_service
from ai.confidence.schemas import (
    CalibrationMetrics,
    CalibratedConfidence,
    RawConfidenceSignal,
)
from backend.app.fixtures.confidence_fixtures import get_all_confidence_fixtures

router = APIRouter(prefix="/confidence", tags=["Confidence & Calibration (Phase 8)"])


class EvaluateConfidenceRequest(BaseModel):
    raw_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Raw model or heuristic score")
    field_name: str = Field("medicine_name", description="Field identifier")
    source: str = Field("multimodal_extraction", description="Signal source")


class EvaluateConfidenceResponse(BaseModel):
    status: str = "success"
    raw_signal: RawConfidenceSignal
    calibrated_confidence: CalibratedConfidence
    calibration_status: str
    message: str


class CalibrationMetricsRequest(BaseModel):
    confidences: List[float] = Field(..., description="List of predicted confidence scores in [0.0, 1.0]")
    labels: List[int] = Field(..., description="List of binary correctness labels (0 or 1)")
    num_bins: Optional[int] = Field(5, ge=2, le=20, description="Number of reliability diagram bins")
    dataset_type: Optional[str] = Field("empirical_evaluation", description="Classification of evaluation data")
    clinical_evidence: Optional[bool] = Field(False, description="Whether metrics constitute clinical calibration evidence")


@router.get("/config")
async def get_confidence_configuration() -> Dict[str, Any]:
    """Returns the active confidence estimation and calibration configuration."""
    service = get_confidence_service()
    return {
        "status": "success",
        "config_version": service.config.config_version,
        "config_hash": service.config_hash,
        "default_calibration_method": service.config.default_calibration_method,
        "min_samples_for_calibration": service.config.min_samples_for_calibration,
        "num_calibration_bins": service.config.num_calibration_bins,
        "calibration_status": service.calibration_status,
        "calibration_model_id": service.calibration_model_id,
        "active_method": service.active_method,
        "is_calibrator_fitted": service.active_calibrator.is_fitted if service.active_calibrator else False,
    }


@router.post("/evaluate", response_model=EvaluateConfidenceResponse)
async def evaluate_confidence_score(payload: EvaluateConfidenceRequest):
    """Evaluates and calibrates a single raw confidence score."""
    service = get_confidence_service()
    raw_sig = RawConfidenceSignal(
        source=payload.source,
        raw_value=payload.raw_score,
        signal_type="api_evaluated_signal",
        model_version=None,
        config_version=service.config.config_version,
    )

    if payload.raw_score is None:
        cal = CalibratedConfidence(
            value=None,
            calibration_method=None,
            calibration_version=None,
            calibration_status="not_available",
        )
        msg = "No raw score provided; calibration is not available."
    elif service.active_calibrator and service.active_calibrator.is_fitted:
        cal = service.active_calibrator.calibrate(payload.raw_score)
        msg = f"Raw score {payload.raw_score:.4f} calibrated to {cal.value:.4f} using {cal.calibration_method}."
    else:
        cal = CalibratedConfidence(
            value=None,
            calibration_method=service.active_method,
            calibration_version=None,
            calibration_status=service.calibration_status,
        )
        msg = f"System calibration status is '{service.calibration_status}'. Raw score is preserved uncalibrated."

    return EvaluateConfidenceResponse(
        status="success",
        raw_signal=raw_sig,
        calibrated_confidence=cal,
        calibration_status=cal.calibration_status,
        message=msg,
    )


@router.post("/metrics", response_model=CalibrationMetrics)
async def compute_empirical_calibration_metrics(payload: CalibrationMetricsRequest):
    """Computes empirical ECE, MCE, Brier score, and reliability diagram bins."""
    if len(payload.confidences) != len(payload.labels):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Length mismatch: {len(payload.confidences)} confidences vs {len(payload.labels)} labels.",
        )
    if not payload.confidences:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot compute metrics on an empty dataset.",
        )

    service = get_confidence_service()
    metrics = service.evaluate_metrics(
        scores=payload.confidences,
        labels=payload.labels,
        num_bins=payload.num_bins,
        dataset_type=payload.dataset_type or "empirical_evaluation",
        clinical_evidence=bool(payload.clinical_evidence),
    )
    return metrics


@router.get("/fixtures")
async def get_phase8_fixtures() -> Dict[str, Any]:
    """Retrieves all 14 deterministic Phase 8 evaluation fixtures."""
    fixtures = get_all_confidence_fixtures()
    return {
        "status": "success",
        "count": len(fixtures),
        "fixture_count": len(fixtures),
        "fixtures": fixtures,
    }
