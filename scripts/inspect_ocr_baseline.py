"""
Phase 5: Research OCR Baseline Inspection Utility
Provides structured visual and textual side-by-side inspection of:
- Original prescription image metadata
- Preprocessed image artifact
- Immutable raw OCR transcription
- Spatial word token bounding boxes and genuine confidence scores
- Comparison with ground-truth reference posology
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend.app.ocr import (
    OCRBaselineConfig,
    OCRBaselineService,
    compute_cer,
    compute_wer,
    normalize_eval_text,
)

SAMPLES_DIR = REPO_ROOT / "data" / "samples"
ANNOTATIONS_FILE = REPO_ROOT / "data" / "annotations" / "sample_annotations.json"


def inspect_sample(
    sample_path: Path,
    variant: str = "enhanced",
    psm: int = 6,
):
    print("=" * 80)
    print("AURA-Rx Research OCR Baseline Inspection")
    print("=" * 80)

    if not sample_path.is_file():
        print(f"Error: Sample file not found at '{sample_path}'")
        return

    # Load annotations for reference
    gt_record = None
    if ANNOTATIONS_FILE.is_file():
        with open(ANNOTATIONS_FILE, "r", encoding="utf-8") as f:
            annotations = json.load(f)
        for doc in annotations:
            img_rel = doc.get("ground_truth", {}).get("image_rel_path", "")
            if Path(img_rel).name == sample_path.name:
                gt_record = doc
                break

    cfg = OCRBaselineConfig(psm=psm, preprocessing_variant=variant)
    service = OCRBaselineService(ocr_config=cfg)

    with open(sample_path, "rb") as f:
        image_bytes = f.read()

    print(f"Input Image:         {sample_path.name}")
    print(f"Input File Size:     {len(image_bytes)} bytes")
    print(f"OCR Engine:          {service.engine.get_version()} (Tesseract)")
    print(f"Engine Languages:    {service.engine.get_available_languages()}")
    print(f"Preproc Variant:     {variant}")
    print(f"Configuration ID:    {cfg.configuration_id}")
    print(f"Configuration Hash:  {cfg.compute_config_hash()[:16]}...")
    print("-" * 80)

    # Run OCR
    result = service.run_ocr(
        image_input=image_bytes,
        filename=sample_path.name,
        preprocessing_variant=variant,
        config_override=cfg,
    )

    print(f"OCR Run ID:          {result.ocr_run_id}")
    print(f"Execution Duration:  {result.duration_seconds:.3f} s")
    print(f"Processing Status:   {result.processing_status}")
    print(f"Source Image SHA256: {result.source_image_sha256[:16]}...")
    print(f"Artifact SHA256:     {result.preprocessing_artifact_sha256[:16]}...")
    print(f"Raw Text SHA256:     {result.raw_text_sha256[:16]}...")
    print(f"Total Tokens:        {len(result.tokens)}")
    print(f"Total Lines:         {len(result.lines)}")
    print("-" * 80)

    # Display Raw OCR Output
    print("\n[IMMUTABLE RAW OCR OUTPUT]:")
    print("+" + "-" * 78 + "+")
    if result.raw_text.strip():
        for line in result.raw_text.splitlines():
            print(f"| {line:<76} |")
    else:
        print(f"| {'(EMPTY OUTPUT PRODUCED BY OCR ENGINE - PRESERVED AS RAW EVIDENCE)':<76} |")
    print("+" + "-" * 78 + "+")

    # Display Ground Truth comparison if available
    if gt_record:
        gt = gt_record.get("ground_truth", {})
        medications = gt.get("medications", [])
        ref_lines = [m.get("raw_text", "") for m in medications if m.get("raw_text")]
        ref_text = "\n".join(ref_lines)

        print("\n[GROUND TRUTH REFERENCE]:")
        print("+" + "-" * 78 + "+")
        for line in ref_lines:
            print(f"| {line:<76} |")
        print("+" + "-" * 78 + "+")

        # Compute Metrics
        cer, char_breakdown = compute_cer(ref_text, result.raw_text)
        wer, word_breakdown = compute_wer(ref_text, result.raw_text)

        print("\n[ERROR RATE METRICS (Calculated on Normalized Representation)]:")
        print(f"  CER (Character Error Rate): {cer:.4f} ({cer*100:.1f}%)")
        print(f"      Substitutions: {char_breakdown.substitutions}, Deletions: {char_breakdown.deletions}, Insertions: {char_breakdown.insertions}")
        print(f"      Ref Length: {char_breakdown.reference_length}, Hyp Length: {char_breakdown.hypothesis_length}")
        print(f"  WER (Word Error Rate):      {wer:.4f} ({wer*100:.1f}%)")
        print(f"      Substitutions: {word_breakdown.substitutions}, Deletions: {word_breakdown.deletions}, Insertions: {word_breakdown.insertions}")
        print(f"      Ref Words: {word_breakdown.reference_length}, Hyp Words: {word_breakdown.hypothesis_length}")

    # Display Extracted Tokens (first 15)
    print(f"\n[EXTRACTED SPATIAL TOKENS (Sample of up to 15 of {len(result.tokens)})]:")
    print(f"{'#':<4} | {'Token Text':<25} | {'Confidence':<12} | {'Bounding Box (x, y, w, h)':<28}")
    print("-" * 78)
    for idx, tok in enumerate(result.tokens[:15], 1):
        conf_str = f"{tok.confidence:.1f}%" if tok.confidence is not None else "null"
        bbox_str = f"({tok.bbox.x}, {tok.bbox.y}, {tok.bbox.width}, {tok.bbox.height})"
        clean_text = tok.text.replace("\n", " ")[:24]
        print(f"{idx:<4} | {clean_text:<25} | {conf_str:<12} | {bbox_str:<28}")

    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Inspect conventional OCR baseline transcription and spatial tokens against ground truth.",
    )
    parser.add_argument(
        "--image",
        type=str,
        default="data/samples/sample_01_clear.png",
        help="Path to prescription image (default: data/samples/sample_01_clear.png)",
    )
    parser.add_argument(
        "--variant",
        type=str,
        default="enhanced",
        choices=["enhanced", "grayscale", "thresholded", "original", "deskewed"],
        help="Preprocessing variant to evaluate (default: enhanced)",
    )
    parser.add_argument(
        "--psm",
        type=int,
        default=6,
        help="Tesseract Page Segmentation Mode (default: 6)",
    )
    args = parser.parse_args()

    target_path = Path(args.image)
    if not target_path.is_absolute():
        target_path = REPO_ROOT / target_path

    inspect_sample(
        sample_path=target_path,
        variant=args.variant,
        psm=args.psm,
    )


if __name__ == "__main__":
    main()
