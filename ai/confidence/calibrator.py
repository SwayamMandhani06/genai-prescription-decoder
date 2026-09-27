"""
Calibration Models for Phase 8: Confidence Estimation & Calibration.
Implements:
1. Platt Scaling (Logistic Sigmoid Calibration)
2. Isotonic Regression (Non-parametric Piecewise Constant Calibration)
3. Temperature Scaling
4. Sample-Size Safeguards (Strict prevention of overfitted calibration on tiny datasets)
"""

import math
import hashlib
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy.optimize import minimize
from sklearn.isotonic import IsotonicRegression

from .schemas import (
    CalibrationMethod,
    CalibrationModelArtifact,
    CalibrationStatus,
    CalibratedConfidence,
)
from .config import get_confidence_config
from .metrics import evaluate_calibration_metrics


class InsufficientDataError(ValueError):
    """Raised when the sample size is below the minimum threshold required for statistical calibration."""
    pass


class BaseCalibrator(ABC):
    """Abstract base class for calibration models."""

    def __init__(
        self,
        model_id: str,
        method_name: CalibrationMethod,
        version: str = "1.0.0",
        min_samples: int = 15,
    ):
        self.model_id = model_id
        self.method_name = method_name
        self.version = version
        self.min_samples = min_samples
        self.is_fitted = False
        self.sample_count = 0
        self.parameters: Dict[str, Any] = {}

    @abstractmethod
    def fit(self, scores: List[float], labels: List[int]) -> "BaseCalibrator":
        """Fits calibration parameters to scores and ground-truth binary labels."""
        pass

    @abstractmethod
    def predict_one(self, score: float) -> float:
        """Transforms a single raw score into a calibrated posterior probability."""
        pass

    def predict_batch(self, scores: List[float]) -> List[float]:
        """Transforms a list of raw scores into calibrated probabilities."""
        return [self.predict_one(s) for s in scores]

    def calibrate(
        self,
        raw_score: Optional[float],
        dataset_version: Optional[str] = None,
    ) -> CalibratedConfidence:
        """
        Calibrates a raw score, returning a fully typed CalibratedConfidence schema.
        Handles uncalibrated and insufficient data states cleanly.
        """
        if raw_score is None:
            return CalibratedConfidence(
                value=None,
                calibration_method=None,
                calibration_version=None,
                calibration_dataset_version=dataset_version,
                calibration_status="not_available",
            )

        if not self.is_fitted:
            return CalibratedConfidence(
                value=None,
                calibration_method=self.method_name,
                calibration_version=self.version,
                calibration_dataset_version=dataset_version,
                calibration_status="insufficient_data",
            )

        calibrated_val = self.predict_one(raw_score)
        return CalibratedConfidence(
            value=round(calibrated_val, 4),
            calibration_method=self.method_name,
            calibration_version=self.version,
            calibration_dataset_version=dataset_version,
            calibration_status="calibrated",
        )

    def export_artifact(
        self,
        dataset_version: str,
        split_seed: int,
        source_signal: str,
        config_hash: str,
        fit_timestamp: str,
        metrics: Optional[Any] = None,
    ) -> CalibrationModelArtifact:
        """Serializes fitted calibration model into an auditable artifact."""
        params_str = json.dumps(self.parameters, sort_keys=True)
        artifact_hash = hashlib.sha256(params_str.encode("utf-8")).hexdigest()[:16]

        return CalibrationModelArtifact(
            calibration_model_id=self.model_id,
            calibration_method=self.method_name,
            calibration_version=self.version,
            source_signal=source_signal,
            dataset_version=dataset_version,
            sample_count=self.sample_count,
            split_seed=split_seed,
            fit_timestamp=fit_timestamp,
            configuration_hash=config_hash,
            model_artifact_hash=artifact_hash,
            parameters=self.parameters,
            metrics=metrics,
        )


class PlattScalingCalibrator(BaseCalibrator):
    """
    Parametric Logistic Calibration (Platt Scaling):
    P(y=1 | s) = 1 / (1 + exp(-(A * s + B)))
    Fits scalar slope A and intercept B by minimizing binary cross-entropy.
    """

    def __init__(
        self,
        model_id: str = "cal_platt_v1",
        version: str = "1.0.0",
        min_samples: int = 15,
    ):
        super().__init__(
            model_id=model_id,
            method_name="platt_scaling",
            version=version,
            min_samples=min_samples,
        )
        self.slope_a: float = 1.0
        self.intercept_b: float = 0.0

    def fit(self, scores: List[float], labels: List[int]) -> "PlattScalingCalibrator":
        n = len(scores)
        if n < self.min_samples:
            self.is_fitted = False
            self.sample_count = n
            raise InsufficientDataError(
                f"Sample count ({n}) is below minimum threshold ({self.min_samples}) for reliable Platt scaling."
            )

        X = np.array(scores, dtype=np.float64)
        y = np.array(labels, dtype=np.float64)

        # Loss function: Binary Cross Entropy with L2 regularization
        def loss_func(params):
            a, b = params
            logits = a * X + b
            # numerically stable sigmoid log-loss
            # loss = log(1 + exp(logits)) - y * logits
            # Use np.logaddexp(0, logits) for stability
            bce = np.mean(np.logaddexp(0, logits) - y * logits)
            reg = 1e-4 * (a ** 2 + b ** 2)
            return bce + reg

        initial_params = [1.0, 0.0]
        res = minimize(loss_func, initial_params, method="L-BFGS-B")

        self.slope_a = float(res.x[0])
        self.intercept_b = float(res.x[1])
        self.parameters = {
            "slope_a": round(self.slope_a, 6),
            "intercept_b": round(self.intercept_b, 6),
            "loss": round(float(res.fun), 6),
        }
        self.is_fitted = True
        self.sample_count = n
        return self

    def predict_one(self, score: float) -> float:
        if not self.is_fitted:
            return float(min(max(score, 0.0), 1.0))
        logit = self.slope_a * score + self.intercept_b
        # Numerically safe sigmoid
        if logit >= 0:
            prob = 1.0 / (1.0 + math.exp(-logit))
        else:
            prob = math.exp(logit) / (1.0 + math.exp(logit))
        return min(max(prob, 0.0), 1.0)


class IsotonicCalibrator(BaseCalibrator):
    """
    Non-parametric Isotonic Regression Calibration:
    Fits a piecewise-constant non-decreasing step function minimizing squared error.
    """

    def __init__(
        self,
        model_id: str = "cal_isotonic_v1",
        version: str = "1.0.0",
        min_samples: int = 15,
    ):
        super().__init__(
            model_id=model_id,
            method_name="isotonic_regression",
            version=version,
            min_samples=min_samples,
        )
        self._iso: Optional[IsotonicRegression] = None

    def fit(self, scores: List[float], labels: List[int]) -> "IsotonicCalibrator":
        n = len(scores)
        if n < self.min_samples:
            self.is_fitted = False
            self.sample_count = n
            raise InsufficientDataError(
                f"Sample count ({n}) is below minimum threshold ({self.min_samples}) for reliable Isotonic regression."
            )

        X = np.array(scores, dtype=np.float64)
        y = np.array(labels, dtype=np.float64)

        self._iso = IsotonicRegression(
            y_min=0.0,
            y_max=1.0,
            increasing=True,
            out_of_bounds="clip",
        )
        self._iso.fit(X, y)

        self.parameters = {
            "thresholds_x": [round(float(x), 4) for x in self._iso.X_thresholds_],
            "thresholds_y": [round(float(y_val), 4) for y_val in self._iso.y_thresholds_],
        }
        self.is_fitted = True
        self.sample_count = n
        return self

    def predict_one(self, score: float) -> float:
        if not self.is_fitted or self._iso is None:
            return float(min(max(score, 0.0), 1.0))
        pred = self._iso.predict([score])[0]
        return min(max(float(pred), 0.0), 1.0)


class TemperatureScalingCalibrator(BaseCalibrator):
    """
    Temperature Scaling Calibration:
    Calibrates logits by scalar temperature parameter T > 0:
    prob = sigmoid(logit(score) / T)
    """

    def __init__(
        self,
        model_id: str = "cal_temp_v1",
        version: str = "1.0.0",
        min_samples: int = 15,
    ):
        super().__init__(
            model_id=model_id,
            method_name="temperature_scaling",
            version=version,
            min_samples=min_samples,
        )
        self.temperature: float = 1.0

    def fit(self, scores: List[float], labels: List[int]) -> "TemperatureScalingCalibrator":
        n = len(scores)
        if n < self.min_samples:
            self.is_fitted = False
            self.sample_count = n
            raise InsufficientDataError(
                f"Sample count ({n}) is below minimum threshold ({self.min_samples}) for Temperature scaling."
            )

        # Convert scores to logits with clipping
        eps = 1e-6
        X_clamped = np.clip(scores, eps, 1.0 - eps)
        logits = np.log(X_clamped / (1.0 - X_clamped))
        y = np.array(labels, dtype=np.float64)

        def loss_func(params):
            t = params[0]
            if t <= 0.01:
                return 1e6
            scaled_logits = logits / t
            bce = np.mean(np.logaddexp(0, scaled_logits) - y * scaled_logits)
            return bce

        res = minimize(loss_func, [1.0], bounds=[(0.05, 10.0)], method="L-BFGS-B")
        self.temperature = float(res.x[0])
        self.parameters = {
            "temperature": round(self.temperature, 4),
            "loss": round(float(res.fun), 6),
        }
        self.is_fitted = True
        self.sample_count = n
        return self

    def predict_one(self, score: float) -> float:
        if not self.is_fitted or self.temperature <= 0:
            return float(min(max(score, 0.0), 1.0))
        eps = 1e-6
        s = min(max(score, eps), 1.0 - eps)
        logit = math.log(s / (1.0 - s))
        scaled_logit = logit / self.temperature
        prob = 1.0 / (1.0 + math.exp(-scaled_logit))
        return min(max(prob, 0.0), 1.0)


class CalibrationFactory:
    """Factory creating and loading calibration models."""

    @staticmethod
    def create(
        method: CalibrationMethod = "platt_scaling",
        model_id: Optional[str] = None,
        min_samples: int = 15,
    ) -> BaseCalibrator:
        if method == "platt_scaling":
            return PlattScalingCalibrator(
                model_id=model_id or "cal_platt_v1",
                min_samples=min_samples,
            )
        elif method == "isotonic_regression":
            return IsotonicCalibrator(
                model_id=model_id or "cal_isotonic_v1",
                min_samples=min_samples,
            )
        elif method == "temperature_scaling":
            return TemperatureScalingCalibrator(
                model_id=model_id or "cal_temp_v1",
                min_samples=min_samples,
            )
        else:
            raise ValueError(f"Unsupported calibration method: {method}")

    @staticmethod
    def from_parameters(
        method: CalibrationMethod,
        parameters: Dict[str, Any],
        model_id: str = "cal_loaded",
        version: str = "1.0.0",
    ) -> BaseCalibrator:
        """Reconstructs a fitted calibrator directly from serialised parameters."""
        calibrator = CalibrationFactory.create(method=method, model_id=model_id)
        calibrator.version = version
        calibrator.parameters = parameters

        if method == "platt_scaling":
            cal = calibrator  # type: PlattScalingCalibrator
            cal.slope_a = float(parameters.get("slope_a", 1.0))
            cal.intercept_b = float(parameters.get("intercept_b", 0.0))
            cal.is_fitted = True
        elif method == "temperature_scaling":
            cal = calibrator  # type: TemperatureScalingCalibrator
            cal.temperature = float(parameters.get("temperature", 1.0))
            cal.is_fitted = True
        elif method == "isotonic_regression":
            cal = calibrator  # type: IsotonicCalibrator
            xs = parameters.get("thresholds_x", [0.0, 1.0])
            ys = parameters.get("thresholds_y", [0.0, 1.0])
            cal._iso = IsotonicRegression(y_min=0.0, y_max=1.0, increasing=True, out_of_bounds="clip")
            cal._iso.fit(xs, ys)
            cal.is_fitted = True

        return calibrator
