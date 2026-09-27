"""
Phase 8: Confidence Estimation & Calibration Package for AURA-Rx.
Transforms visual extraction and retrieval signals into calibrated confidence estimates
evaluated against known ground truth outcomes.
"""

from .schemas import (
    RawConfidenceSignal,
    CalibratedConfidence,
    FieldConfidenceAssessment,
    MedicineIdentityConfidence,
    DosageConfidenceAssessment,
    MedicineConfidenceAssessment,
    PrescriptionConfidenceAssessment,
    CalibrationBin,
    CalibrationMetrics,
    CalibrationComparison,
    CalibrationModelArtifact,
    ConfidenceState,
)
from .config import ConfidenceConfig, get_confidence_config
from .calibrator import (
    BaseCalibrator,
    PlattScalingCalibrator,
    IsotonicCalibrator,
    TemperatureScalingCalibrator,
    CalibrationFactory,
)
from .metrics import (
    compute_ece,
    compute_mce,
    compute_brier_score,
    compute_nll,
    compute_calibration_bins,
    evaluate_calibration_metrics,
)
from .signals import (
    extract_field_confidence_signal,
    extract_dosage_confidence_signal,
    extract_medicine_identity_confidence,
    detect_confidence_conflicts,
)
from .service import (
    ConfidenceEstimationService,
    get_confidence_service,
)

__all__ = [
    "RawConfidenceSignal",
    "CalibratedConfidence",
    "FieldConfidenceAssessment",
    "MedicineIdentityConfidence",
    "DosageConfidenceAssessment",
    "MedicineConfidenceAssessment",
    "PrescriptionConfidenceAssessment",
    "CalibrationBin",
    "CalibrationMetrics",
    "CalibrationComparison",
    "CalibrationModelArtifact",
    "ConfidenceState",
    "ConfidenceConfig",
    "get_confidence_config",
    "BaseCalibrator",
    "PlattScalingCalibrator",
    "IsotonicCalibrator",
    "TemperatureScalingCalibrator",
    "CalibrationFactory",
    "compute_ece",
    "compute_mce",
    "compute_brier_score",
    "compute_nll",
    "compute_calibration_bins",
    "evaluate_calibration_metrics",
    "extract_field_confidence_signal",
    "extract_dosage_confidence_signal",
    "extract_medicine_identity_confidence",
    "detect_confidence_conflicts",
    "ConfidenceEstimationService",
    "get_confidence_service",
]
