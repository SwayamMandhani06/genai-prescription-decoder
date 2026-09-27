"""
Comprehensive Dataset Validation Suite (Phase 3)
Verifies image readability, headers, corruptions, duplicate hashes, schema validity, and split leakage.
"""

import hashlib
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from pydantic import BaseModel, Field

from PIL import Image

from .schema import PrescriptionDocumentRecord
from .splitter import DatasetSplitResult, detect_split_leakage


class IssueSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"


class ValidationIssue(BaseModel):
    severity: IssueSeverity
    code: str
    message: str
    document_id: Optional[str] = None
    field: Optional[str] = None


class ImageHeuristics(BaseModel):
    file_path: str
    file_size_bytes: int
    format: str
    width: int
    height: int
    mode: str
    aspect_ratio: float
    dpi: Optional[Tuple[float, float]] = None
    sha256: str
    is_corrupted: bool = False


class ValidationReport(BaseModel):
    """Structured report produced by dataset audit."""
    total_inspected: int = 0
    valid_records_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    is_valid: bool = True
    issues: List[ValidationIssue] = Field(default_factory=list)
    image_heuristics: Dict[str, ImageHeuristics] = Field(default_factory=dict)
    duplicate_image_hashes: Dict[str, List[str]] = Field(default_factory=dict)
    leakage_summary: Optional[Dict[str, Any]] = None

    def add_issue(self, severity: IssueSeverity, code: str, message: str, doc_id: Optional[str] = None, field: Optional[str] = None):
        issue = ValidationIssue(severity=severity, code=code, message=message, document_id=doc_id, field=field)
        self.issues.append(issue)
        if severity == IssueSeverity.ERROR:
            self.error_count += 1
            self.is_valid = False
        else:
            self.warning_count += 1


class DatasetValidator:
    """Rigorous audit utility for dataset manifests, images, and ground-truth schemas."""

    SUPPORTED_FORMATS = {"PNG", "JPEG", "TIFF", "WEBP"}
    MIN_RESOLUTION = (150, 150)
    MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25MB

    @classmethod
    def validate_image_file(cls, path: Path) -> Tuple[Optional[ImageHeuristics], List[ValidationIssue]]:
        """Inspects an image on disk for readability, header validity, corruption, and dimensions."""
        issues: List[ValidationIssue] = []
        if not path.exists():
            issues.append(ValidationIssue(
                severity=IssueSeverity.ERROR,
                code="FILE_NOT_FOUND",
                message=f"Image file does not exist: {path}"
            ))
            return None, issues

        file_size = path.stat().st_size
        if file_size == 0:
            issues.append(ValidationIssue(
                severity=IssueSeverity.ERROR,
                code="EMPTY_FILE",
                message=f"Image file is empty (0 bytes): {path}"
            ))
            return None, issues

        if file_size > cls.MAX_FILE_SIZE_BYTES:
            issues.append(ValidationIssue(
                severity=IssueSeverity.WARNING,
                code="EXCESSIVE_FILE_SIZE",
                message=f"Image file exceeds 25MB ({file_size / (1024*1024):.1f}MB): {path}"
            ))

        # Compute SHA-256
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        file_hash = hasher.hexdigest()

        # Inspect using Pillow
        try:
            with Image.open(path) as img:
                img_format = (img.format or "UNKNOWN").upper()
                width, height = img.size
                mode = img.mode
                info = img.info
                dpi = info.get("dpi")

                # Verify image stream integrity
                img.verify()

            # Format check
            if img_format not in cls.SUPPORTED_FORMATS:
                issues.append(ValidationIssue(
                    severity=IssueSeverity.ERROR,
                    code="UNSUPPORTED_FORMAT",
                    message=f"Format '{img_format}' is not among supported {cls.SUPPORTED_FORMATS}: {path}"
                ))

            # Dimension check
            if width < cls.MIN_RESOLUTION[0] or height < cls.MIN_RESOLUTION[1]:
                issues.append(ValidationIssue(
                    severity=IssueSeverity.WARNING,
                    code="LOW_RESOLUTION",
                    message=f"Image resolution ({width}x{height}) is below recommended {cls.MIN_RESOLUTION}: {path}"
                ))

            heuristics = ImageHeuristics(
                file_path=str(path),
                file_size_bytes=file_size,
                format=img_format,
                width=width,
                height=height,
                mode=mode,
                aspect_ratio=round(width / max(height, 1), 3),
                dpi=dpi,
                sha256=file_hash,
                is_corrupted=False,
            )
            return heuristics, issues

        except Exception as exc:
            issues.append(ValidationIssue(
                severity=IssueSeverity.ERROR,
                code="CORRUPTED_IMAGE",
                message=f"Failed to read image or image stream corrupted: {exc} ({path})"
            ))
            heuristics = ImageHeuristics(
                file_path=str(path),
                file_size_bytes=file_size,
                format="CORRUPTED",
                width=0,
                height=0,
                mode="UNKNOWN",
                aspect_ratio=0.0,
                sha256=file_hash,
                is_corrupted=True,
            )
            return heuristics, issues

    @classmethod
    def audit_collection(
        cls,
        records: List[PrescriptionDocumentRecord],
        base_data_dir: Path,
        split: Optional[DatasetSplitResult] = None,
    ) -> ValidationReport:
        """Runs a complete validation audit over a collection of prescription document records."""
        report = ValidationReport(total_inspected=len(records))
        hash_to_docs: Dict[str, List[str]] = {}

        for rec in records:
            doc_id = rec.document_id
            gt = rec.ground_truth

            # Privacy validation
            if not gt.patient_deidentified:
                report.add_issue(
                    IssueSeverity.ERROR,
                    "PII_RISK_IDENTIFIED",
                    "Record fails de-identification certification.",
                    doc_id=doc_id,
                    field="patient_deidentified"
                )

            # Medication list completeness
            if not gt.medications:
                report.add_issue(
                    IssueSeverity.WARNING,
                    "NO_MEDICATIONS_ANNOTATED",
                    "Document contains zero prescribed medications.",
                    doc_id=doc_id
                )

            # Image path resolution
            img_path = base_data_dir / gt.image_rel_path
            heuristics, img_issues = cls.validate_image_file(img_path)
            for iss in img_issues:
                report.add_issue(iss.severity, iss.code, iss.message, doc_id=doc_id)

            if heuristics:
                report.image_heuristics[doc_id] = heuristics
                # Verify SHA-256 match between ground truth record and image bytes
                if gt.image_sha256 != heuristics.sha256:
                    report.add_issue(
                        IssueSeverity.ERROR,
                        "IMAGE_CHECKSUM_MISMATCH",
                        f"Checksum mismatch: ground truth expects {gt.image_sha256[:12]}, file has {heuristics.sha256[:12]}",
                        doc_id=doc_id,
                        field="image_sha256"
                    )
                # Track for duplicate detection
                hash_to_docs.setdefault(heuristics.sha256, []).append(doc_id)

        # Duplicate image hash detection
        duplicates = {h: docs for h, docs in hash_to_docs.items() if len(docs) > 1}
        if duplicates:
            report.duplicate_image_hashes = duplicates
            for h, docs in duplicates.items():
                report.add_issue(
                    IssueSeverity.WARNING,
                    "DUPLICATE_IMAGE_HASH",
                    f"Identical image SHA-256 {h[:12]} shared by documents: {docs}"
                )

        # Split leakage audit
        if split:
            leakage = detect_split_leakage(split, records)
            report.leakage_summary = leakage
            if not leakage["is_leak_free"]:
                if leakage["has_group_leakage"]:
                    report.add_issue(
                        IssueSeverity.ERROR,
                        "SPLIT_LEAKAGE_GROUP",
                        f"Group-level leakage detected across partitions: {leakage['leaked_groups']}"
                    )
                if leakage["has_hash_leakage"]:
                    report.add_issue(
                        IssueSeverity.ERROR,
                        "SPLIT_LEAKAGE_HASH",
                        f"Exact image duplicate leakage detected across partitions: {leakage['leaked_hashes']}"
                    )

        report.valid_records_count = report.total_inspected - (report.error_count)
        return report
