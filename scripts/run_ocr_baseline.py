"""
Phase 5: Reproducible OCR/HTR Baseline Experiment Runner
Executes conventional OCR baseline across evaluation samples and preprocessing variants.
Computes CER, WER, and field entity metrics against ground truth.
Saves reproducible experiment artifacts to eval/baseline_outputs.json.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend.app.ocr import (
    OCRBaselineConfig,
    OCRBaselineService,
    OCRRunResult,
    compute_cer,
    compute_wer,
    compute_entity_metrics,
    evaluate_ocr_hypothesis,
    normalize_eval_text,
)

SAMPLES_DIR = REPO_ROOT / "data" / "samples"
ANNOTATIONS_FILE = REPO_ROOT / "data" / "annotations" / "sample_annotations.json"
DEFAULT_OUTPUT_FILE = REPO_ROOT / "eval" / "baseline_outputs.json"


def load_ground_truth_map() -> Dict[str, Dict[str, Any]]:
    """
    Loads ground truth annotations indexed by image filename and document_id.
    """
    if not ANNOTATIONS_FILE.is_file():
        return {}

    with open(ANNOTATIONS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    gt_map = {}
    for doc in data:
        doc_id = doc.get("document_id")
        gt = doc.get("ground_truth", {})
        img_rel = gt.get("image_rel_path", "")
        img_filename = Path(img_rel).name if img_rel else ""

        # Extract full reference text by combining medication lines
        medications = gt.get("medications", [])
        ref_lines = [m.get("raw_text", "") for m in medications if m.get("raw_text")]
        full_ref_text = "\n".join(ref_lines)

        # Extract entity lists
        medicine_names = [m.get("medicine_name", "") for m in medications if m.get("medicine_name")]
        dosages = [m.get("dosage_strength", "") for m in medications if m.get("dosage_strength")]
        frequencies = [m.get("frequency", "") for m in medications if m.get("frequency")]
        durations = [m.get("duration", "") for m in medications if m.get("duration")]

        record = {
            "document_id": doc_id,
            "image_filename": img_filename,
            "full_ref_text": full_ref_text,
            "entities": {
                "medicine_name": medicine_names,
                "dosage": dosages,
                "frequency": frequencies,
                "duration": durations,
            },
            "scenario": doc.get("metadata", {}).get("scenario", ""),
        }

        if doc_id:
            gt_map[doc_id] = record
        if img_filename:
            gt_map[img_filename] = record

    return gt_map


def run_experiment(
    input_paths: List[Path],
    config: OCRBaselineConfig,
    compare_variants: bool = False,
    variants: Optional[List[str]] = None,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Executes the OCR baseline across the given input image paths.
    """
    service = OCRBaselineService(ocr_config=config)
    gt_map = load_ground_truth_map()

    target_variants = variants or ["enhanced", "grayscale", "thresholded", "original", "deskewed"]
    if not compare_variants:
        target_variants = [config.preprocessing_variant]

    experiment_records: List[Dict[str, Any]] = []

    print("\n" + "=" * 80)
    print("AURA-Rx Phase 5: Conventional OCR/HTR Baseline Experiment")
    print("=" * 80)
    print(f"Engine:             {service.engine.get_version()} ({service.engine.config.engine})")
    print(f"Configuration ID:   {config.configuration_id}")
    print(f"Config Hash:        {config.compute_config_hash()[:16]}...")
    print(f"Languages:          {service.engine.get_available_languages()}")
    print(f"Variants:           {', '.join(target_variants)}")
    print(f"Input Samples:      {len(input_paths)}")
    print("=" * 80)

    for img_path in sorted(input_paths):
        filename = img_path.name
        gt_info = gt_map.get(filename, {})
        doc_id = gt_info.get("document_id", filename)
        ref_text = gt_info.get("full_ref_text")
        entities = gt_info.get("entities")

        print(f"\nProcessing: {filename} (Doc ID: {doc_id})")

        with open(img_path, "rb") as f:
            image_bytes = f.read()

        if compare_variants:
            comp_results = service.run_variant_comparison(
                image_bytes=image_bytes,
                filename=filename,
                variants=target_variants,
            )
            for var_name, res in comp_results.items():
                eval_metrics = None
                if ref_text:
                    eval_metrics = service.evaluate_run(
                        run_result=res,
                        ground_truth_text=ref_text,
                        ground_truth_entities=entities,
                    )

                rec = {
                    "sample_id": filename,
                    "document_id": doc_id,
                    "variant": var_name,
                    "ocr_run_id": res.ocr_run_id,
                    "source_image_sha256": res.source_image_sha256,
                    "artifact_sha256": res.preprocessing_artifact_sha256,
                    "raw_text": res.raw_text,
                    "raw_text_sha256": res.raw_text_sha256,
                    "token_count": len(res.tokens),
                    "status": res.processing_status,
                    "duration_seconds": res.duration_seconds,
                    "metrics": eval_metrics.model_dump() if eval_metrics else None,
                }
                experiment_records.append(rec)
                cer_str = f"{eval_metrics.cer:.4f}" if (eval_metrics and eval_metrics.cer is not None) else "N/A"
                wer_str = f"{eval_metrics.wer:.4f}" if (eval_metrics and eval_metrics.wer is not None) else "N/A"
                print(f"  [{var_name:12s}] Tokens: {len(res.tokens):3d} | Status: {res.processing_status:9s} | CER: {cer_str:7s} | WER: {wer_str:7s} | Dur: {res.duration_seconds:.2f}s")

        else:
            res = service.run_ocr(
                image_input=image_bytes,
                filename=filename,
                preprocessing_variant=config.preprocessing_variant,
                config_override=config,
            )
            eval_metrics = None
            if ref_text:
                eval_metrics = service.evaluate_run(
                    run_result=res,
                    ground_truth_text=ref_text,
                    ground_truth_entities=entities,
                )

            rec = {
                "sample_id": filename,
                "document_id": doc_id,
                "variant": config.preprocessing_variant,
                "ocr_run_id": res.ocr_run_id,
                "source_image_sha256": res.source_image_sha256,
                "artifact_sha256": res.preprocessing_artifact_sha256,
                "raw_text": res.raw_text,
                "raw_text_sha256": res.raw_text_sha256,
                "token_count": len(res.tokens),
                "status": res.processing_status,
                "duration_seconds": res.duration_seconds,
                "metrics": eval_metrics.model_dump() if eval_metrics else None,
            }
            experiment_records.append(rec)
            cer_str = f"{eval_metrics.cer:.4f}" if (eval_metrics and eval_metrics.cer is not None) else "N/A"
            wer_str = f"{eval_metrics.wer:.4f}" if (eval_metrics and eval_metrics.wer is not None) else "N/A"
            print(f"  [{config.preprocessing_variant:12s}] Tokens: {len(res.tokens):3d} | Status: {res.processing_status:9s} | CER: {cer_str:7s} | WER: {wer_str:7s} | Dur: {res.duration_seconds:.2f}s")

    # Aggregate metrics across samples where ground truth was evaluated
    evaluated_records = [r for r in experiment_records if r.get("metrics") and r["metrics"].get("cer") is not None]
    summary_by_variant: Dict[str, Dict[str, Any]] = {}

    for var in set(r["variant"] for r in experiment_records):
        var_recs = [r for r in evaluated_records if r["variant"] == var]
        if var_recs:
            avg_cer = sum(r["metrics"]["cer"] for r in var_recs) / len(var_recs)
            avg_wer = sum(r["metrics"]["wer"] for r in var_recs) / len(var_recs)
            summary_by_variant[var] = {
                "sample_count": len(var_recs),
                "mean_cer": round(avg_cer, 4),
                "mean_wer": round(avg_wer, 4),
            }

    output_payload = {
        "benchmark_metadata": {
            "phase": "Phase 5 - Conventional OCR/HTR Baseline",
            "role": "Calibration & Integration Sample Evaluation (N=7; not a statistically sufficient research benchmark)",
            "engine": {
                "name": "tesseract",
                "version": service.engine.get_version(),
                "languages": service.engine.get_available_languages(),
            },
            "configuration": {
                "id": config.configuration_id,
                "hash": config.compute_config_hash(),
                "language": config.language,
                "psm": config.psm,
                "oem": config.oem,
                "preserve_raw_evidence": config.preserve_raw_evidence,
            },
        },
        "summary_by_variant": summary_by_variant,
        "runs": experiment_records,
    }

    # Save to disk
    out_file = output_path or DEFAULT_OUTPUT_FILE
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    print("\n" + "=" * 80)
    print(f"Results successfully written to: {out_file}")
    if summary_by_variant:
        print("\nSummary By Preprocessing Variant:")
        for var, s in summary_by_variant.items():
            print(f"  Variant: {var:12s} | N={s['sample_count']} | Mean CER: {s['mean_cer']:.4f} | Mean WER: {s['mean_wer']:.4f}")
    print("=" * 80)

    return output_payload


def main():
    parser = argparse.ArgumentParser(
        description="AURA-Rx Phase 5: Conventional OCR/HTR Baseline Runner",
    )
    parser.add_argument(
        "--samples",
        action="store_true",
        help="Run across the 7 local AURA-Rx calibration & integration samples",
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Path to a single prescription image",
    )
    parser.add_argument(
        "--variant",
        type=str,
        default="enhanced",
        choices=["enhanced", "grayscale", "thresholded", "original", "deskewed"],
        help="Target preprocessing variant (default: enhanced)",
    )
    parser.add_argument(
        "--compare-variants",
        action="store_true",
        help="Run controlled comparison across all 5 preprocessing variants",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT_FILE),
        help="Output JSON path (default: eval/baseline_outputs.json)",
    )
    parser.add_argument(
        "--psm",
        type=int,
        default=6,
        help="Tesseract Page Segmentation Mode (default: 6)",
    )

    args = parser.parse_args()

    # Determine input images
    input_paths: List[Path] = []
    if args.input:
        p = Path(args.input)
        if not p.is_file():
            print(f"Error: input file '{args.input}' does not exist.")
            sys.exit(1)
        input_paths.append(p)
    elif args.samples or True:  # Default to samples if no input provided
        if not SAMPLES_DIR.is_dir():
            print(f"Error: samples directory '{SAMPLES_DIR}' does not exist.")
            sys.exit(1)
        input_paths = sorted(list(SAMPLES_DIR.glob("*.png")))

    if not input_paths:
        print("No images found to process.")
        sys.exit(1)

    cfg = OCRBaselineConfig(
        psm=args.psm,
        preprocessing_variant=args.variant,
    )

    out_path = Path(args.output)
    run_experiment(
        input_paths=input_paths,
        config=cfg,
        compare_variants=args.compare_variants,
        output_path=out_path,
    )


if __name__ == "__main__":
    main()
