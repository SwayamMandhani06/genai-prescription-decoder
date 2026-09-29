"""
EXP-01: Conventional OCR Baseline Evaluator (Section 9, 10, 11).
Evaluates Phase 5 Tesseract baseline runs across preprocessing variants against ground truth.
Generates eval/tables/01_ocr_baseline.csv and per-sample breakdown.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

from eval.ocr.metrics import compute_cer, compute_wer


class OCREvaluator:
    def __init__(self, root_dir: Optional[Path] = None):
        if root_dir is None:
            self.root_dir = Path(__file__).resolve().parent.parent.parent
        else:
            self.root_dir = root_dir

        self.baseline_file = self.root_dir / "eval" / "baseline_outputs.json"
        self.annotations_file = self.root_dir / "data" / "annotations" / "sample_annotations.json"

    def _load_ground_truth(self) -> Dict[str, str]:
        gt_map = {}
        if self.annotations_file.exists():
            with open(self.annotations_file, "r", encoding="utf-8") as f:
                annotations = json.load(f)
                for item in annotations:
                    doc_id = item.get("document_id")
                    meds = item.get("ground_truth", {}).get("medications", [])
                    raw_lines = [m.get("raw_text", "") for m in meds if m.get("raw_text")]
                    gt_text = "\n".join(raw_lines)
                    gt_map[doc_id] = gt_text
        return gt_map

    def evaluate(self) -> Dict[str, Any]:
        gt_map = self._load_ground_truth()
        
        runs_data = []
        if self.baseline_file.exists():
            with open(self.baseline_file, "r", encoding="utf-8") as f:
                baseline_data = json.load(f)
                runs_data = baseline_data.get("runs", [])

        per_sample_results: List[Dict[str, Any]] = []
        variant_groups: Dict[str, List[Dict[str, Any]]] = {}

        for run in runs_data:
            doc_id = run.get("document_id")
            variant = run.get("variant", "original")
            raw_text = run.get("raw_text", "")
            gt_text = gt_map.get(doc_id, "")

            cer_metrics = compute_cer(gt_text, raw_text)
            wer_metrics = compute_wer(gt_text, raw_text)

            sample_eval = {
                "sample_id": run.get("sample_id"),
                "document_id": doc_id,
                "variant": variant,
                "cer": cer_metrics["cer"],
                "wer": wer_metrics["wer"],
                "char_accuracy": cer_metrics["char_accuracy"],
                "word_accuracy": wer_metrics["word_accuracy"],
                "ref_chars": cer_metrics["ref_length"],
                "hyp_chars": cer_metrics["hyp_length"],
                "ref_words": wer_metrics["ref_words"],
                "hyp_words": wer_metrics["hyp_words"],
                "subs_chars": cer_metrics["substitutions"],
                "dels_chars": cer_metrics["deletions"],
                "ins_chars": cer_metrics["insertions"],
            }
            per_sample_results.append(sample_eval)

            if variant not in variant_groups:
                variant_groups[variant] = []
            variant_groups[variant].append(sample_eval)

        # Aggregate summary per variant
        summary_by_variant = {}
        for var, items in variant_groups.items():
            cers = [x["cer"] for x in items]
            wers = [x["wer"] for x in items]
            summary_by_variant[var] = {
                "sample_count": len(items),
                "mean_cer": round(float(np.mean(cers)), 4),
                "median_cer": round(float(np.median(cers)), 4),
                "std_cer": round(float(np.std(cers)), 4),
                "mean_wer": round(float(np.mean(wers)), 4),
                "median_wer": round(float(np.median(wers)), 4),
                "std_wer": round(float(np.std(wers)), 4),
            }

        return {
            "experiment_id": "EXP-01",
            "name": "Conventional OCR Baseline Evaluation",
            "engine": "tesseract-5.4.0",
            "sample_count": len(per_sample_results),
            "summary_by_variant": summary_by_variant,
            "per_sample": per_sample_results
        }

    def generate_csv_table(self, output_dir: Path) -> Path:
        results = self.evaluate()
        output_dir.mkdir(parents=True, exist_ok=True)
        table_path = output_dir / "01_ocr_baseline.csv"

        headers = ["Variant", "Samples", "Mean CER", "Median CER", "Std CER", "Mean WER", "Median WER", "Std WER"]
        rows = []
        for var, metrics in results["summary_by_variant"].items():
            rows.append([
                var,
                str(metrics["sample_count"]),
                f"{metrics['mean_cer']:.4f}",
                f"{metrics['median_cer']:.4f}",
                f"{metrics['std_cer']:.4f}",
                f"{metrics['mean_wer']:.4f}",
                f"{metrics['median_wer']:.4f}",
                f"{metrics['std_wer']:.4f}"
            ])

        with open(table_path, "w", encoding="utf-8") as f:
            f.write(",".join(headers) + "\n")
            for r in rows:
                f.write(",".join(r) + "\n")

        return table_path
