"""
Unit tests for Phase 7 Reference Data Ingestion and Integrity Verification.
Adheres to Section 17 of PLAN.md.
"""

import pytest
from pathlib import Path
from ai.rag.ingestion import ReferenceIngestor, compute_file_sha256
from ai.rag.sources import AUTHORITATIVE_SOURCES, CDSCO_SOURCE_ID, RXNORM_SOURCE_ID, get_source_provenance
from ai.rag.schemas import MedicineReferenceRecord


class TestRAGIngestion:
    def test_authoritative_sources_documented(self):
        assert CDSCO_SOURCE_ID in AUTHORITATIVE_SOURCES
        assert RXNORM_SOURCE_ID in AUTHORITATIVE_SOURCES

        cdsco = get_source_provenance(CDSCO_SOURCE_ID)
        assert cdsco.source_id == "cdsco-approved-drugs"
        assert "Open Government Data License" in cdsco.license
        assert cdsco.license_category == "statutory_government_open_data"

        rxnorm = get_source_provenance(RXNORM_SOURCE_ID)
        assert rxnorm.source_id == "nlm-rxnorm"
        assert "UMLS" in rxnorm.license
        assert rxnorm.license_category == "clinical_terminology_license"

    def test_unauthorized_source_rejection(self):
        with pytest.raises(ValueError, match="Unauthorized reference source"):
            get_source_provenance("unknown-unlicensed-source")

    def test_manifest_loading_and_record_counts(self):
        ingestor = ReferenceIngestor(base_dir=Path("."))
        manifest = ingestor.load_manifest("data/reference/reference_manifest.json")
        assert manifest["manifest_version"] == "1.0.0"
        assert len(manifest["reference_sources"]) >= 2
        assert manifest["summary"]["total_records"] == 30

    def test_full_ingestion_and_checksum_verification(self):
        ingestor = ReferenceIngestor(base_dir=Path("."))
        records, report = ingestor.ingest_all(
            manifest_rel_path="data/reference/reference_manifest.json",
            verify_checksums=True
        )
        assert len(records) == 30
        assert report.valid_records_count == 30
        assert report.duplicate_records_detected == 0
        assert len(report.schema_errors) == 0
        assert report.checksum_verifications.get(CDSCO_SOURCE_ID) is True
        assert report.checksum_verifications.get(RXNORM_SOURCE_ID) is True

    def test_record_schema_and_provenance_preservation(self):
        ingestor = ReferenceIngestor(base_dir=Path("."))
        records, _ = ingestor.ingest_all(verify_checksums=False)
        for record in records:
            assert isinstance(record, MedicineReferenceRecord)
            assert record.reference_id.startswith("REF-")
            assert record.source in (CDSCO_SOURCE_ID, RXNORM_SOURCE_ID)
            assert record.medicine_name
            assert record.normalized_name
            assert record.provenance.source_id == record.source
            assert record.provenance.license
