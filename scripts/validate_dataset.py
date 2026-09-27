"""
CLI Dataset Validation Tool (Phase 3)
Audits dataset manifests, image integrity, ground-truth annotations, and split leakage.
"""

import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.dataset.schema import PrescriptionDocumentRecord
from backend.app.dataset.manifest import load_manifest
from backend.app.dataset.splitter import DatasetSplitResult
from backend.app.dataset.validator import DatasetValidator, IssueSeverity


def main():
    base_data_dir = Path("data")
    manifest_p = base_data_dir / "manifests" / "dataset_manifest.json"
    annotations_p = base_data_dir / "annotations" / "sample_annotations.json"
    splits_p = base_data_dir / "splits" / "sample_splits.json"

    print("======================================================")
    print("AURA-Rx DATASET & EXPERIMENTAL INFRASTRUCTURE AUDIT")
    print(f"Data Root: {base_data_dir.resolve()}")
    print("======================================================")

    # 1. Manifest audit
    print("\n--- 1. Auditing Dataset Manifest ---")
    if not manifest_p.exists():
        print(f"  [FAIL] Manifest missing: {manifest_p}")
        sys.exit(1)
    manifest = load_manifest(manifest_p)
    print(f"  [PASS] Manifest loaded successfully (v{manifest.manifest_version})")
    print(f"  [INFO] Cataloged sources: {len(manifest.sources)}")
    for s in manifest.sources:
        print(f"         - {s.dataset_id} [{s.verification_status.value}]: {s.name} ({s.provenance.license})")

    # 2. Annotations & Images audit
    print("\n--- 2. Auditing Ground Truth Annotations & Physical Images ---")
    if not annotations_p.exists():
        print(f"  [FAIL] Annotations missing: {annotations_p}")
        sys.exit(1)
    with open(annotations_p, "r", encoding="utf-8") as f:
        raw_recs = json.load(f)
    records = [PrescriptionDocumentRecord.model_validate(r) for r in raw_recs]
    print(f"  [PASS] Parsed {len(records)} gold-standard ground truth records.")

    # 3. Splits audit
    print("\n--- 3. Auditing Dataset Splits & Leakage ---")
    split = None
    if splits_p.exists():
        with open(splits_p, "r", encoding="utf-8") as f:
            split_data = json.load(f)
        split = DatasetSplitResult.model_validate(split_data)
        print(f"  [PASS] Splits loaded: Train={len(split.train_ids)}, Val={len(split.val_ids)}, Test={len(split.test_ids)}")

    # 4. Comprehensive audit via DatasetValidator
    report = DatasetValidator.audit_collection(records, base_data_dir, split=split)

    print("\n--- 4. Validation Report Summary ---")
    print(f"  Total documents inspected: {report.total_inspected}")
    print(f"  Valid records count:      {report.valid_records_count}")
    print(f"  Errors encountered:       {report.error_count}")
    print(f"  Warnings encountered:     {report.warning_count}")

    if report.duplicate_image_hashes:
        print(f"  Duplicate image hashes:   {len(report.duplicate_image_hashes)}")

    if report.leakage_summary:
        leak_free = report.leakage_summary["is_leak_free"]
        status_str = "[PASS] Zero leakage across splits" if leak_free else "[FAIL] Leakage detected"
        print(f"  Split Leakage Audit:      {status_str}")

    if report.issues:
        print("\n--- Diagnostic Issues Log ---")
        for iss in report.issues:
            prefix = "[ERROR]" if iss.severity == IssueSeverity.ERROR else "[WARN]"
            doc_str = f" [{iss.document_id}]" if iss.document_id else ""
            print(f"  {prefix}{doc_str} ({iss.code}): {iss.message}")

    print("\n======================================================")
    if report.is_valid:
        print("AUDIT STATUS: ALL CHECKS PASSED (VALID)")
        print("======================================================")
        return 0
    else:
        print("AUDIT STATUS: CRITICAL ERRORS DETECTED (INVALID)")
        print("======================================================")
        return 1


if __name__ == "__main__":
    sys.exit(main())
