"""
Phase 4: Preprocessing & Quality Inspection Research Tool
CLI utility for visual debugging, quality metrics inspection,
and artifact comparison across calibration prescription samples.

Usage:
    python scripts/inspect_preprocessing.py
    python scripts/inspect_preprocessing.py --image data/samples/sample_01_clear.png
"""

import argparse
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.preprocessing import ImagePreprocessingService, PreprocessingConfig


def generate_side_by_side_comparison(
    original_pil: Image.Image,
    derived_images: dict,
    output_path: Path,
    title: str,
):
    """
    Creates a multi-panel visual debugging sheet showing Original vs Derived representations.
    """
    panels = [
        ("Original Input", original_pil.convert("RGB")),
        ("Grayscale", derived_images.get("grayscale")),
        ("Illum. Normalized", derived_images.get("normalized")),
        ("Median Denoised", derived_images.get("denoised")),
        ("Contrast Enhanced", derived_images.get("enhanced")),
        ("Sauvola Binary", derived_images.get("thresholded")),
    ]
    panels = [(lbl, img) for lbl, img in panels if img is not None]

    num_panels = len(panels)
    target_w, target_h = 300, 380

    composite_w = num_panels * target_w + (num_panels + 1) * 10
    composite_h = target_h + 60

    composite = Image.new("RGB", (composite_w, composite_h), color=(24, 28, 36))
    draw = ImageDraw.Draw(composite)

    # Header
    draw.text((15, 10), title, fill=(240, 240, 240))

    for idx, (label, img) in enumerate(panels):
        thumb = img.convert("RGB").resize((target_w, target_h), Image.Resampling.BILINEAR)
        x_offset = 10 + idx * (target_w + 10)
        y_offset = 40
        composite.paste(thumb, (x_offset, y_offset))
        draw.text((x_offset + 5, y_offset + 5), label, fill=(0, 255, 200))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    composite.save(output_path, format="PNG")


def inspect_image(image_path: Path, service: ImagePreprocessingService, output_base: Path):
    print(f"\n{'='*70}")
    print(f"INSPECTING: {image_path.name}")
    print(f"{'='*70}")

    image_bytes = image_path.read_bytes()
    prescription_id = f"INSPECT-{image_path.stem.upper()}"

    metadata, report = service.validate_and_assess(image_bytes, image_path.name)

    print(f"Dimensions:    {metadata.width} x {metadata.height} ({metadata.aspect_ratio})")
    print(f"Color Mode:    {metadata.color_mode} ({metadata.channels} channels)")
    print(f"Eff. Density:  {metadata.effective_ppi} PPI (heuristic)")
    print(f"SHA-256:       {metadata.original_sha256[:16]}...")
    print(f"Quality State: [{report.overall_status.upper()}] (Heuristic Score: {report.heuristic_quality_score})")

    print("\nOptical Metrics:")
    for metric_name, data in report.metrics.items():
        status = data.get("status", "N/A")
        print(f"  - {metric_name.capitalize():<14}: Status={status:<14} Details={data}")

    if report.issues:
        print("\n[!] Critical Quality Issues:")
        for iss in report.issues:
            print(f"    * {iss}")

    if report.warnings:
        print("\n[*] Quality Degradation Warnings:")
        for w in report.warnings:
            print(f"    * {w}")

    # Process and store derived artifacts
    res, manifest, pub_url = service.process_and_store(
        image_bytes=image_bytes,
        filename=image_path.name,
        prescription_id=prescription_id,
        reject_insufficient_quality=False,
    )

    print(f"\nDerived Artifacts Saved to: data/processed/preprocessing_runs/{prescription_id}/")
    for art in manifest.artifacts:
        print(f"  + {art.type:<12}: {art.width}x{art.height}px | SHA256={art.sha256[:12]}...")

    # Generate multi-panel comparison image
    with Image.open(image_path) as orig_pil:
        comp_path = output_base / prescription_id / "visual_comparison.png"
        generate_side_by_side_comparison(
            original_pil=orig_pil,
            derived_images=res.derived_images,
            output_path=comp_path,
            title=f"AURA-Rx Preprocessing Inspection - {image_path.name} [{report.overall_status.upper()}]",
        )
        print(f"Visual Debugging Sheet: {comp_path}")


def main():
    parser = argparse.ArgumentParser(description="AURA-Rx Preprocessing Inspection Tool")
    parser.add_argument("--image", type=str, help="Path to specific image file to inspect")
    args = parser.parse_args()

    service = ImagePreprocessingService()
    runs_dir = Path("data/processed/preprocessing_runs")

    if args.image:
        target = Path(args.image)
        if not target.exists():
            print(f"Error: Target image '{target}' not found.")
            sys.exit(1)
        inspect_image(target, service, runs_dir)
    else:
        # Inspect all calibration samples
        samples_dir = Path("data/samples")
        sample_files = sorted(samples_dir.glob("sample_*.png"))
        if not sample_files:
            print(f"No samples found in {samples_dir}")
            sys.exit(1)

        print(f"Starting inspection over {len(sample_files)} calibration samples...")
        for p in sample_files:
            inspect_image(p, service, runs_dir)

    print(f"\n{'='*70}")
    print("PREPROCESSING INSPECTION COMPLETE.")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
