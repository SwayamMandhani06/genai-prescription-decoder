"""
EXP-04: Confidence Calibration Evaluator (Section 18, 19, 20).
Evaluates Phase 8 confidence estimation, conformal calibration, and reliability diagrams.
Computes ECE, MCE, Brier score, and binning metrics.
Generates eval/tables/04_calibration.csv.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

from ai.confidence.metrics import compute_calibration_bins, evaluate_calibration_metrics
from backend.app.fixtures.confidence_fixtures import get_all_confidence_fixtures


class ConfidenceEvaluator:
    def __init__(self, root_dir: Optional[Path] = None):
        if root_dir is None:
            self.root_dir = Path(__file__).resolve().parent.parent.parent
        else:
            self.root_dir = root_dir

    def evaluate(self) -> Dict[str, Any]:
        fixtures = get_all_confidence_fixtures()

        raw_confs = []
        cal_confs = []
        labels = []
        fixture_records = []

        # Synthetic ground truth labels mapped to fixture scenarios
        # Case 1 (well-calibrated): 1
        # Case 2 (overconfident): 0
        # Case 3 (underconfident): 1
        # Case 4 (ambiguous 0.5): 0
        correctness_map = {
            "CASE-08-01-WELL-CALIBRATED-HIGH": 1,
            "CASE-08-02-OVERCONFIDENT": 0,
            "CASE-08-03-UNDERCONFIDENT": 1,
            "CASE-08-04-PERFECTLY-AMBIGUOUS": 0,
            "CASE-08-05-INSUFFICIENT-DATA": 1,
            "CASE-08-08-MEDICINE-NAME": 1,
            "CASE-08-09-DOSAGE-VISUAL-ONLY": 1,
            "CASE-08-10-FREQUENCY-HIGH": 1,
            "CASE-08-11-DURATION-HIGH": 1,
            "CASE-08-13-CONFLICTING-SIGNALS": 0,
            "CASE-08-14-REFERENCE-MATCH-VISUAL-UNCERTAIN": 0
        }

        for f in fixtures:
            fix_id = f.get("fixture_id")
            raw_sig = f.get("raw_signal")
            cal_obj = f.get("calibrated")

            if raw_sig and fix_id in correctness_map:
                r_val = raw_sig.get("raw_value")
                c_val = cal_obj.get("value") if cal_obj else None
                lbl = correctness_map[fix_id]

                raw_confs.append(r_val)
                labels.append(lbl)
                if c_val is not None:
                    cal_confs.append(c_val)
                else:
                    cal_confs.append(r_val)  # fallback to raw for comparison

                fixture_records.append({
                    "fixture_id": fix_id,
                    "scenario": f.get("scenario"),
                    "raw_confidence": r_val,
                    "calibrated_confidence": c_val,
                    "ground_truth_label": lbl
                })

        num_samples = len(raw_confs)

        # Compute calibration metrics
        raw_metrics = evaluate_calibration_metrics(raw_confs, labels, num_bins=5)
        cal_metrics = evaluate_calibration_metrics(cal_confs, labels, num_bins=5)

        raw_bins = [b.model_dump() for b in raw_metrics.bins]
        cal_bins = [b.model_dump() for b in cal_metrics.bins]

        return {
            "experiment_id": "EXP-04",
            "name": "Confidence Estimation & Calibration Evaluation",
            "dataset_type": "synthetic_verification",
            "clinical_evidence": False,
            "sample_count": num_samples,
            "min_samples_threshold": 15,
            "calibration_status": "insufficient_data_on_dev_cohort",
            "limitation_statement": (
                "The values are calibration-method verification results and are not empirical clinical "
                "calibration evidence. For the actual N=7 AURA-Rx cohort, the insufficient_data safeguard "
                "(N < 15) prevents reliable empirical calibration claims per Section 20 of PLAN.md."
            ),
            "raw_metrics": {
                "ece": round(raw_metrics.ece, 4),
                "mce": round(raw_metrics.mce, 4),
                "brier_score": round(raw_metrics.brier_score, 4),
                "negative_log_likelihood": round(raw_metrics.nll, 4) if raw_metrics.nll else None,
                "bins": raw_bins
            },
            "calibrated_metrics": {
                "ece": round(cal_metrics.ece, 4),
                "mce": round(cal_metrics.mce, 4),
                "brier_score": round(cal_metrics.brier_score, 4),
                "negative_log_likelihood": round(cal_metrics.nll, 4) if cal_metrics.nll else None,
                "bins": cal_bins
            },
            "per_fixture": fixture_records
        }

    def generate_csv_table(self, output_dir: Path) -> Path:
        results = self.evaluate()
        output_dir.mkdir(parents=True, exist_ok=True)
        table_path = output_dir / "04_calibration.csv"

        headers = ["Model / Metric Type", "Samples (N)", "ECE", "MCE", "Brier Score", "NLL", "Dataset Type", "Clinical Evidence", "Calibration Status"]
        raw = results["raw_metrics"]
        cal = results["calibrated_metrics"]

        rows = [
            [
                "Raw Confidence (Uncalibrated)",
                str(results["sample_count"]),
                f"{raw['ece']:.4f}",
                f"{raw['mce']:.4f}",
                f"{raw['brier_score']:.4f}",
                f"{raw['negative_log_likelihood']:.4f}" if raw["negative_log_likelihood"] else "N/A",
                "synthetic_verification",
                "False",
                "uncalibrated"
            ],
            [
                "Platt / Isotonic Calibrated",
                str(results["sample_count"]),
                f"{cal['ece']:.4f}",
                f"{cal['mce']:.4f}",
                f"{cal['brier_score']:.4f}",
                f"{cal['negative_log_likelihood']:.4f}" if cal["negative_log_likelihood"] else "N/A",
                "synthetic_verification",
                "False",
                results["calibration_status"]
            ]
        ]

        with open(table_path, "w", encoding="utf-8") as f:
            f.write(",".join(headers) + "\n")
            for r in rows:
                f.write(",".join(r) + "\n")

        return table_path
