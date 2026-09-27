"""
Dataset Manifest and Provenance Management (Phase 3)
Tracks data sources, licensing, permitted usage, verification status, and cryptographic hashes.
"""

import json
import hashlib
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class SourceVerificationStatus(str, Enum):
    """Verification grade of candidate data source."""
    VERIFIED_PUBLIC = "verified_public"          # Verified open-access research dataset
    VERIFIED_REGULATORY = "verified_regulatory"  # Verified official regulatory authority gazette
    CANDIDATE_UNVERIFIED = "candidate_unverified"# Identified source undergoing licensing or format review


class LicenseCategory(str, Enum):
    """Specific legal instrument category governing data or reference assets."""
    OPEN_DATASET_LICENSE = "open_dataset_license"                  # Standard open content/data license (e.g. CC BY 4.0)
    ACADEMIC_RESEARCH_LICENSE = "academic_research_license"        # Restricted non-commercial academic research license (e.g. CC BY-NC 4.0)
    STATUTORY_GOVERNMENT_OPEN_DATA = "statutory_government_open_data" # Official statutory government open data framework
    CLINICAL_TERMINOLOGY_LICENSE = "clinical_terminology_license"  # Specialized medical nomenclature license (e.g. UMLS Metathesaurus)
    CLINICAL_SAFETY_GUIDANCE = "clinical_safety_guidance"          # Non-statutory clinical practice advisory / safety guidance (e.g. ISMP)
    OPEN_SOURCE_SOFTWARE_DATA_LICENSE = "open_source_software_data_license" # Permissive OSS project data license (e.g. MIT Academic)
    UNVERIFIED_PENDING_AUDIT = "unverified_pending_audit"          # Unverified or pending licensing investigation


class ProvenanceRecord(BaseModel):
    """Provenance tracking record for legal traceability and auditability."""
    source_url: str = Field(..., description="Canonical URL or DOI reference")
    provider_organization: str = Field(..., description="Publishing university, agency, or research group")
    retrieval_date: str = Field(..., description="ISO 8601 date of retrieval or inspection")
    license: str = Field(..., description="Software/Data license (e.g. 'CC-BY-4.0', 'Open Government Data')")
    license_category: LicenseCategory = Field(..., description="Legal instrument classification")
    permitted_usage: str = Field(..., description="Summary of legal permitted scope (e.g. 'Academic Research & Evaluation')")
    attribution_requirements: str = Field(..., description="Specific citation or attribution string required")
    citation: str = Field(..., description="Formal academic citation or technical publication reference")
    dataset_version: Optional[str] = Field("1.0", description="Upstream provider version or release tag")
    archive_checksum: Optional[str] = Field(None, description="SHA-256 hash of downloaded raw archive if applicable")


class DatasetSourceEntry(BaseModel):
    """Inventory entry for a discrete dataset or regulatory reference corpus."""
    dataset_id: str = Field(..., min_length=3, description="Canonical internal slug (e.g. 'bd-handwritten-rx')")
    name: str = Field(..., min_length=3, description="Official dataset title")
    description: str = Field(..., description="Detailed description of clinical scope and content")
    document_type: str = Field(..., description="Prescription pad scan, synthetic form, or vocabulary lexicon")
    handwriting_characteristics: str = Field(..., description="Cursive doctor hand, semi-print, stroke variation")
    language_script: str = Field(..., description="Writing script (e.g. 'Latin cursive with Bengali notes')")
    available_annotations: str = Field(..., description="Document-level, token bounding box, or transcription text")
    verification_status: SourceVerificationStatus = Field(..., description="Licensing and authenticity verification status")
    access_method: str = Field(..., description="Public download URL, portal registration, or API query")
    known_limitations: List[str] = Field(default_factory=list, description="Explicit catalog of limitations")
    relevance: str = Field(..., description="Functional role in AURA-Rx research pipeline")
    provenance: ProvenanceRecord = Field(..., description="Detailed provenance and licensing documentation")


class DatasetManifest(BaseModel):
    """
    Machine-readable dataset manifest cataloging all approved, candidate,
    and reference data sources used in the project.
    """
    manifest_version: str = Field(default="1.0.0", description="Semantic version of manifest schema")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 generation timestamp"
    )
    project_identifier: str = Field(default="AURA-Rx-GenAI-Prescription-Decoder", description="Project slug")
    sources: List[DatasetSourceEntry] = Field(default_factory=list, description="Cataloged dataset sources")
    local_sample_count: int = Field(default=0, ge=0, description="Number of verified local evaluation samples")
    checksum: Optional[str] = Field(None, description="SHA-256 checksum of the manifest contents")

    def compute_hash(self) -> str:
        """Computes a deterministic SHA-256 hash of all sources and sample counts."""
        payload = json.dumps(
            {
                "manifest_version": self.manifest_version,
                "project_identifier": self.project_identifier,
                "sources": [s.model_dump() for s in self.sources],
                "local_sample_count": self.local_sample_count,
            },
            sort_keys=True
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def update_checksum(self) -> None:
        """Calculates and stores self-checksum."""
        self.checksum = self.compute_hash()


def load_manifest(manifest_path: Path) -> DatasetManifest:
    """Loads and validates a DatasetManifest from a JSON file."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    manifest = DatasetManifest.model_validate(data)
    return manifest


def save_manifest(manifest: DatasetManifest, manifest_path: Path) -> None:
    """Persists a DatasetManifest with updated checksum."""
    manifest.update_checksum()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest.model_dump(), f, indent=2, ensure_ascii=False)
