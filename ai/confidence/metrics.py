"""
Calibration Metrics for Phase 8: Confidence Estimation & Calibration.
Implements mathematically rigorous evaluation of:
- Expected Calibration Error (ECE)
- Maximum Calibration Error (MCE)
- Brier Score (Mean Squared Error)
- Negative Log-Likelihood (NLL)
- Reliability Diagram Binned Partitions
"""

import math
from typing import List, Optional
from .schemas import CalibrationBin, CalibrationMetrics


def compute_calibration_bins(
    confidences: List[float],
    labels: List[int],
    num_bins: int = 5,
) -> List[CalibrationBin]:
    """
    Partitions predictions into num_bins equal-width confidence intervals over [0.0, 1.0].
    Computes count, mean predicted confidence, empirical accuracy, and gap for each bin.
    """
    if len(confidences) != len(labels):
        raise ValueError(
            f"Length mismatch between confidences ({len(confidences)}) and labels ({len(labels)})"
        )

    if num_bins < 1:
        raise ValueError(f"num_bins must be >= 1, received {num_bins}")

    bins_data: List[CalibrationBin] = []
    bin_width = 1.0 / num_bins

    for b in range(num_bins):
        lower = b * bin_width
        upper = (b + 1) * bin_width

        # In last bin, include upper boundary 1.0; otherwise [lower, upper)
        bin_confs: List[float] = []
        bin_labels: List[int] = []

        for conf, label in zip(confidences, labels):
            conf_clamped = min(max(conf, 0.0), 1.0)
            if b == num_bins - 1:
                in_bin = (lower <= conf_clamped <= upper)
            else:
                in_bin = (lower <= conf_clamped < upper)

            if in_bin:
                bin_confs.append(conf_clamped)
                bin_labels.append(label)

        count = len(bin_confs)
        if count > 0:
            mean_conf = sum(bin_confs) / count
            accuracy = sum(bin_labels) / count
            gap = abs(accuracy - mean_conf)
        else:
            mean_conf = (lower + upper) / 2.0
            accuracy = 0.0
            gap = 0.0

        bins_data.append(
            CalibrationBin(
                bin_index=b,
                lower_bound=round(lower, 4),
                upper_bound=round(upper, 4),
                count=count,
                mean_confidence=round(mean_conf, 4),
                empirical_accuracy=round(accuracy, 4),
                calibration_gap=round(gap, 4),
            )
        )

    return bins_data


def compute_ece(
    confidences: List[float],
    labels: List[int],
    num_bins: int = 5,
) -> float:
    """
    Computes the Expected Calibration Error (ECE):
    ECE = sum_{m=1}^M (|B_m| / N) * |acc(B_m) - conf(B_m)|
    """
    if not confidences:
        return 0.0

    bins = compute_calibration_bins(confidences, labels, num_bins=num_bins)
    total_samples = len(confidences)

    ece = 0.0
    for b in bins:
        if b.count > 0:
            weight = b.count / total_samples
            ece += weight * b.calibration_gap

    return round(ece, 4)


def compute_mce(
    confidences: List[float],
    labels: List[int],
    num_bins: int = 5,
) -> float:
    """
    Computes the Maximum Calibration Error (MCE):
    MCE = max_{m: |B_m| > 0} |acc(B_m) - conf(B_m)|
    """
    if not confidences:
        return 0.0

    bins = compute_calibration_bins(confidences, labels, num_bins=num_bins)
    non_empty_gaps = [b.calibration_gap for b in bins if b.count > 0]

    return round(max(non_empty_gaps), 4) if non_empty_gaps else 0.0


def compute_brier_score(
    confidences: List[float],
    labels: List[int],
) -> float:
    """
    Computes the Brier Score (Mean Squared Error against ground truth):
    Brier = (1 / N) * sum_{i=1}^N (conf_i - label_i)^2
    Lower is better; 0.0 is perfect probabilistic prediction.
    """
    if not confidences:
        return 0.0

    if len(confidences) != len(labels):
        raise ValueError(
            f"Length mismatch: {len(confidences)} confidences vs {len(labels)} labels"
        )

    squared_errors = [
        (min(max(c, 0.0), 1.0) - y) ** 2
        for c, y in zip(confidences, labels)
    ]
    return round(sum(squared_errors) / len(squared_errors), 4)


def compute_nll(
    confidences: List[float],
    labels: List[int],
    eps: float = 1e-12,
) -> Optional[float]:
    """
    Computes Negative Log-Likelihood (Binary Cross Entropy):
    NLL = - (1 / N) * sum_{i=1}^N [y_i * ln(p_i) + (1 - y_i) * ln(1 - p_i)]
    """
    if not confidences:
        return None

    if len(confidences) != len(labels):
        raise ValueError(
            f"Length mismatch: {len(confidences)} confidences vs {len(labels)} labels"
        )

    loss_sum = 0.0
    for c, y in zip(confidences, labels):
        p = min(max(c, eps), 1.0 - eps)
        loss = y * math.log(p) + (1 - y) * math.log(1.0 - p)
        loss_sum -= loss

    return round(loss_sum / len(confidences), 4)


def evaluate_calibration_metrics(
    confidences: List[float],
    labels: List[int],
    num_bins: int = 5,
    dataset_type: str = "empirical_evaluation",
    clinical_evidence: bool = False,
) -> CalibrationMetrics:
    """
    Evaluates complete calibration metrics for a set of predictions and ground-truth labels.
    Explicitly tracks whether evaluation is synthetic or clinical evidence.
    """
    bins = compute_calibration_bins(confidences, labels, num_bins=num_bins)
    ece = compute_ece(confidences, labels, num_bins=num_bins)
    mce = compute_mce(confidences, labels, num_bins=num_bins)
    brier = compute_brier_score(confidences, labels)
    nll = compute_nll(confidences, labels)

    return CalibrationMetrics(
        ece=ece,
        mce=mce,
        brier_score=brier,
        nll=nll,
        sample_count=len(confidences),
        bin_count=num_bins,
        bins=bins,
        dataset_type=dataset_type,
        clinical_evidence=clinical_evidence,
    )
