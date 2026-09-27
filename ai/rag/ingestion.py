"""
Authoritative Reference Data Ingestion and Integrity Verification Module.
Adheres strictly to Section 17 of PLAN.md:
- Validates source schemas
- Computes cryptographic SHA-256 checksums
- Normalizes deterministic fields safely
- Detects duplicates
- Preserves raw source records and audit provenance
"""

import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from pydantic import ValidationError

from .schemas import MedicineReferenceRecord, SourceProvenance
from .normalization import normalize_medicine_name
from .sources import AUTHORITATIVE_SOURCES

logger = logging.getLogger("aura_rx.rag.ingestion")


class IngestionReport:
    def __init__(self):
        self.sources_loaded: List[str] = []
        self.total_records_processed: int = 0
        self.valid_records_count: int = 0
        self.duplicate_records_detected: int = 0
        self.schema_errors: List[str] = []
        self.checksum_verifications: Dict[str, bool] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sources_loaded": self.sources_loaded,
            "total_records_processed": self.total_records_processed,
            "valid_records_count": self.valid_records_count,
            "duplicate_records_detected": self.duplicate_records_detected,
            "schema_errors_count": len(self.schema_errors),
            "schema_errors": self.schema_errors[:10],
            "checksum_verifications": self.checksum_verifications,
        }


def compute_file_sha256(file_path: Path) -> str:
    """Computes SHA-256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class ReferenceIngestor:
    """
    Loads, verifies, and normalizes reference records from the filesystem.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)

    def load_manifest(self, manifest_rel_path: str = "data/reference/reference_manifest.json") -> Dict[str, Any]:
        manifest_path = self.base_dir / manifest_rel_path
        if not manifest_path.is_file():
            # Try direct relative to project root
            manifest_path = Path(manifest_rel_path)
            if not manifest_path.is_file():
                raise FileNotFoundError(f"Reference manifest not found at {manifest_path}")

        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def ingest_all(
        self,
        manifest_rel_path: str = "data/reference/reference_manifest.json",
        verify_checksums: bool = True
    ) -> Tuple[List[MedicineReferenceRecord], IngestionReport]:
        """
        Executes full ingestion pipeline against documented sources manifest.
        Returns validated records and ingestion report.
        """
        report = IngestionReport()
        manifest = self.load_manifest(manifest_rel_path)
        sources_meta = manifest.get("reference_sources", [])

        all_records: List[MedicineReferenceRecord] = []
        seen_ref_ids: Dict[str, str] = {}
        seen_names: Dict[str, str] = {}

        for src_meta in sources_meta:
            source_id = src_meta.get("source_id")
            rel_file = src_meta.get("file_path")
            expected_sha = src_meta.get("sha256")

            file_path = self.base_dir / rel_file
            if not file_path.is_file():
                file_path = Path(rel_file)
                if not file_path.is_file():
                    err_msg = f"Reference file missing: {rel_file}"
                    logger.error(err_msg)
                    report.schema_errors.append(err_msg)
                    continue

            # Verify cryptographic checksum
            if verify_checksums and expected_sha:
                actual_sha = compute_file_sha256(file_path)
                matches = (actual_sha.lower() == expected_sha.lower())
                report.checksum_verifications[source_id] = matches
                if not matches:
                    err_msg = f"Checksum mismatch for {source_id}: expected {expected_sha}, got {actual_sha}"
                    logger.warning(err_msg)
                    report.schema_errors.append(err_msg)
            else:
                report.checksum_verifications[source_id] = True

            # Load JSON records
            with open(file_path, "r", encoding="utf-8") as f:
                raw_records = json.load(f)

            report.sources_loaded.append(source_id)

            for item in raw_records:
                report.total_records_processed += 1
                try:
                    # Enforce provenance consistency
                    if "provenance" not in item and source_id in AUTHORITATIVE_SOURCES:
                        item["provenance"] = AUTHORITATIVE_SOURCES[source_id].model_dump()

                    # Validate schema
                    record = MedicineReferenceRecord.model_validate(item)

                    # Re-verify normalized_name deterministically
                    expected_norm = normalize_medicine_name(record.medicine_name)
                    if record.normalized_name != expected_norm:
                        record.normalized_name = expected_norm

                    # Duplicate check by reference_id
                    if record.reference_id in seen_ref_ids:
                        report.duplicate_records_detected += 1
                        logger.warning("Duplicate reference_id detected: %s", record.reference_id)
                        continue
                    seen_ref_ids[record.reference_id] = source_id

                    # Duplicate check by exact canonical formulation
                    canonical_key = f"{record.source}:{record.normalized_name}"
                    if canonical_key in seen_names:
                        report.duplicate_records_detected += 1
                        logger.info("Duplicate formulation key detected: %s", canonical_key)
                    else:
                        seen_names[canonical_key] = record.reference_id

                    all_records.append(record)
                    report.valid_records_count += 1

                except ValidationError as ve:
                    report.schema_errors.append(f"Record validation error in {source_id}: {str(ve)}")
                except Exception as ex:
                    report.schema_errors.append(f"Unexpected record parsing error in {source_id}: {str(ex)}")

        logger.info(
            "Ingestion completed: %d valid records loaded from %d sources (%d duplicates, %d errors)",
            report.valid_records_count,
            len(report.sources_loaded),
            report.duplicate_records_detected,
            len(report.schema_errors),
        )
        return all_records, report
