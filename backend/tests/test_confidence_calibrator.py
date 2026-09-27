"""
Unit tests for Phase 8 Calibration Models.
Verifies:
- Platt Scaling (logistic sigmoid)
- Isotonic Regression (monotonic step)
- Temperature Scaling
- Minimum sample size threshold guard (InsufficientDataError)
- CalibrationFactory export and reconstruction
"""

import pytest
import numpy as np
from ai.confidence.calibrator import (
    PlattScalingCalibrator,
    IsotonicCalibrator,
    TemperatureScalingCalibrator,
    CalibrationFactory,
    InsufficientDataError,
)
from ai.confidence.schemas import CalibrationModelArtifact


class TestConfidenceCalibrator:
    @pytest.fixture
    def synthetic_calibration_data(self):
        # 30 synthetic samples with known overconfidence pattern
        # Raw scores: [0.6, 0.95], labels: 70% 1s, 30% 0s
        np.random.seed(42)
        scores = [
            0.55, 0.60, 0.62, 0.65, 0.70, 0.72, 0.75, 0.78, 0.80, 0.82,
            0.85, 0.86, 0.88, 0.90, 0.92, 0.93, 0.94, 0.95, 0.96, 0.98,
        ]
        labels = [
            0, 0, 1, 0, 1, 0, 1, 1, 1, 1,
            0, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        ]
        return scores, labels

    def test_platt_scaling_fitting_and_prediction(self, synthetic_calibration_data):
        scores, labels = synthetic_calibration_data
        cal = PlattScalingCalibrator(model_id="test_platt", min_samples=15)
        cal.fit(scores, labels)

        assert cal.is_fitted is True
        assert "slope_a" in cal.parameters
        assert "intercept_b" in cal.parameters
        assert cal.sample_count == 20

        # Predict one
        pred = cal.predict_one(0.85)
        assert 0.0 <= pred <= 1.0

        # Predict batch
        preds = cal.predict_batch([0.60, 0.80, 0.95])
        assert len(preds) == 3
        assert preds[0] <= preds[1] <= preds[2]  # Monotonically increasing for positive slope

    def test_platt_scaling_insufficient_data_rejection(self):
        cal = PlattScalingCalibrator(model_id="test_small", min_samples=15)
        small_scores = [0.8, 0.9, 0.7]
        small_labels = [1, 1, 0]

        with pytest.raises(InsufficientDataError, match="below minimum threshold"):
            cal.fit(small_scores, small_labels)

        assert cal.is_fitted is False
        # When uncalibrated, calibrate() returns insufficient_data status
        res = cal.calibrate(0.85)
        assert res.value is None
        assert res.calibration_status == "insufficient_data"

    def test_isotonic_regression_fitting_and_monotonicity(self, synthetic_calibration_data):
        scores, labels = synthetic_calibration_data
        cal = IsotonicCalibrator(model_id="test_iso", min_samples=15)
        cal.fit(scores, labels)

        assert cal.is_fitted is True
        assert "thresholds_x" in cal.parameters
        assert "thresholds_y" in cal.parameters

        # Verify monotonicity
        p1 = cal.predict_one(0.60)
        p2 = cal.predict_one(0.75)
        p3 = cal.predict_one(0.95)
        assert p1 <= p2 <= p3

    def test_temperature_scaling_fitting(self, synthetic_calibration_data):
        scores, labels = synthetic_calibration_data
        cal = TemperatureScalingCalibrator(model_id="test_temp", min_samples=15)
        cal.fit(scores, labels)

        assert cal.is_fitted is True
        assert cal.temperature > 0.0
        assert "temperature" in cal.parameters

        pred = cal.predict_one(0.80)
        assert 0.0 <= pred <= 1.0

    def test_calibrator_export_artifact(self, synthetic_calibration_data):
        scores, labels = synthetic_calibration_data
        cal = PlattScalingCalibrator(model_id="test_export", version="1.2.0", min_samples=15)
        cal.fit(scores, labels)

        artifact = cal.export_artifact(
            dataset_version="1.0.0",
            split_seed=42,
            source_signal="multimodal_raw_logprob",
            config_hash="abc123hash",
            fit_timestamp="2026-09-27T00:00:00Z",
        )
        assert isinstance(artifact, CalibrationModelArtifact)
        assert artifact.calibration_model_id == "test_export"
        assert artifact.calibration_version == "1.2.0"
        assert artifact.sample_count == 20
        assert len(artifact.model_artifact_hash) == 16

    def test_calibration_factory_reconstruction_from_parameters(self):
        params = {"slope_a": 1.45, "intercept_b": -0.25}
        cal = CalibrationFactory.from_parameters(
            method="platt_scaling",
            parameters=params,
            model_id="reconstructed_platt",
        )
        assert cal.is_fitted is True
        pred = cal.predict_one(0.80)
        assert 0.0 <= pred <= 1.0
