"""
Unit tests for Phase 8 Calibration Metrics.
Verifies mathematical correctness of:
- compute_ece
- compute_mce
- compute_brier_score
- compute_nll
- compute_calibration_bins
- evaluate_calibration_metrics
"""

import pytest
import math
from ai.confidence.metrics import (
    compute_ece,
    compute_mce,
    compute_brier_score,
    compute_nll,
    compute_calibration_bins,
    evaluate_calibration_metrics,
)


class TestConfidenceMetrics:
    def test_perfect_calibration_ece_zero(self):
        # 10 samples: 5 predicted at 0.0 with label 0, 5 predicted at 1.0 with label 1
        confidences = [0.0] * 5 + [1.0] * 5
        labels = [0] * 5 + [1] * 5
        ece = compute_ece(confidences, labels, num_bins=2)
        assert ece == 0.0
        mce = compute_mce(confidences, labels, num_bins=2)
        assert mce == 0.0
        brier = compute_brier_score(confidences, labels)
        assert brier == 0.0

    def test_severe_miscalibration_high_ece(self):
        # Overconfident: all predicted at 0.95, but all labels are 0
        confidences = [0.95] * 10
        labels = [0] * 10
        ece = compute_ece(confidences, labels, num_bins=5)
        # Gap is 0.95 - 0.0 = 0.95
        assert ece == pytest.approx(0.95, abs=0.01)
        mce = compute_mce(confidences, labels, num_bins=5)
        assert mce == pytest.approx(0.95, abs=0.01)

    def test_brier_score_properties(self):
        # Perfect predictions -> 0.0
        assert compute_brier_score([1.0, 0.0], [1, 0]) == 0.0
        # Completely wrong predictions -> 1.0
        assert compute_brier_score([1.0, 0.0], [0, 1]) == 1.0
        # Guessing 0.5 -> 0.25
        assert compute_brier_score([0.5, 0.5], [1, 0]) == 0.25

    def test_nll_properties(self):
        # Confident correct -> low loss
        nll_correct = compute_nll([0.99, 0.01], [1, 0])
        assert nll_correct is not None
        assert nll_correct < 0.05

        # Confident wrong -> high loss
        nll_wrong = compute_nll([0.99, 0.01], [0, 1])
        assert nll_wrong is not None
        assert nll_wrong > 3.0

    def test_calibration_bins_partition(self):
        confidences = [0.1, 0.3, 0.5, 0.7, 0.9]
        labels = [0, 0, 1, 1, 1]
        bins = compute_calibration_bins(confidences, labels, num_bins=5)

        assert len(bins) == 5
        total_count = sum(b.count for b in bins)
        assert total_count == 5

        # Check bin boundaries
        assert bins[0].lower_bound == 0.0
        assert bins[0].upper_bound == 0.2
        assert bins[0].count == 1
        assert bins[0].empirical_accuracy == 0.0
        assert bins[0].mean_confidence == 0.1

        assert bins[4].lower_bound == 0.8
        assert bins[4].upper_bound == 1.0
        assert bins[4].count == 1
        assert bins[4].empirical_accuracy == 1.0
        assert bins[4].mean_confidence == 0.9

    def test_evaluate_calibration_metrics_bundle(self):
        confidences = [0.8, 0.9, 0.2, 0.3]
        labels = [1, 1, 0, 0]
        res = evaluate_calibration_metrics(confidences, labels, num_bins=2)
        assert res.sample_count == 4
        assert res.bin_count == 2
        assert res.ece >= 0.0
        assert res.mce >= 0.0
        assert res.brier_score >= 0.0
        assert res.nll is not None
        assert len(res.bins) == 2
        assert res.dataset_type == "empirical_evaluation"
        assert res.clinical_evidence is False

    def test_synthetic_verification_metrics_flags(self):
        res = evaluate_calibration_metrics(
            [0.8, 0.9],
            [1, 1],
            num_bins=2,
            dataset_type="synthetic_verification",
            clinical_evidence=False,
        )
        assert res.dataset_type == "synthetic_verification"
        assert res.clinical_evidence is False

    def test_empty_dataset_handling(self):
        assert compute_ece([], []) == 0.0
        assert compute_mce([], []) == 0.0
        assert compute_brier_score([], []) == 0.0
        assert compute_nll([], []) is None
