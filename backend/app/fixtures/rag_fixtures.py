"""
Phase 7 RAG Medicine Validation Mock Fixtures.
Deterministic fixtures covering all 14 required test cases specified in Section 22 of PLAN.md.
ALL DATA IN THIS FILE IS STRICTLY SYNTHETIC MOCK/TEST DATA.
"""

from typing import Dict, Any, List
from ai.rag.schemas import (
    MedicineReferenceRecord,
    RetrievalCandidate,
    MedicineValidationResult,
    ValidationDecisionProvenance,
    SourceProvenance,
)

# Common Mock Provenance
MOCK_CDSCO_PROVENANCE = SourceProvenance(
    source_id="mock-cdsco-test",
    source_name="MOCK CDSCO Approved Drug Formulations [TEST ONLY]",
    source_version="2024.1-mock",
    license="Open Government Data License - India (Test Fixture)",
    license_category="statutory_government_open_data",
    retrieval_date="2026-09-27T00:00:00Z",
    citation="CDSCO Mock Reference Dataset for Testing. Not for clinical use.",
    source_url="https://mock.cdsco.gov.in/test"
)

MOCK_RXNORM_PROVENANCE = SourceProvenance(
    source_id="mock-rxnorm-test",
    source_name="MOCK NLM RxNorm Clinical Nomenclature [TEST ONLY]",
    source_version="2024-08-mock",
    license="UMLS Metathesaurus License (Test Fixture)",
    license_category="clinical_terminology_license",
    retrieval_date="2026-09-27T00:00:00Z",
    citation="NLM Mock Clinical Reference for Testing. Not for clinical use.",
    source_url="https://mock.nlm.nih.gov/rxnorm/test"
)


# ------------------------------------------------------------------------------
# 1. Exact medicine match
# ------------------------------------------------------------------------------
def get_exact_match_fixture() -> Dict[str, Any]:
    return {
        "case_id": "case_1_exact_match",
        "description": "Exact match between extracted medicine candidate and canonical reference title",
        "is_mock_test_data": True,
        "input": {
            "candidate_name": "Augmentin 625 Duo",
            "observed_dosage": "625 mg",
        },
        "expected": {
            "validation_status": "validated",
            "matched_entity_name": "Augmentin 625 Duo",
            "requires_human_review": False,
            "match_method": "exact_normalized_name",
        }
    }


# ------------------------------------------------------------------------------
# 2. Exact normalized match
# ------------------------------------------------------------------------------
def get_exact_normalized_match_fixture() -> Dict[str, Any]:
    return {
        "case_id": "case_2_exact_normalized_match",
        "description": "Exact match achieved after case-folding, unicode NFKC, and whitespace collapse",
        "is_mock_test_data": True,
        "input": {
            "candidate_name": "  augmentin   625 duo  ",
            "observed_dosage": "625 mg",
        },
        "expected": {
            "validation_status": "validated",
            "matched_entity_name": "Augmentin 625 Duo",
            "requires_human_review": False,
        }
    }


# ------------------------------------------------------------------------------
# 3. Alias match
# ------------------------------------------------------------------------------
def get_alias_match_fixture() -> Dict[str, Any]:
    return {
        "case_id": "case_3_alias_match",
        "description": "Candidate matches an authorized documented commercial alias/synonym",
        "is_mock_test_data": True,
        "input": {
            "candidate_name": "Clavam 625",
            "observed_dosage": "625 mg",
        },
        "expected": {
            "validation_status": "validated",
            "matched_entity_name": "Augmentin 625 Duo",
            "match_method": "exact_alias",
            "requires_human_review": False,
        }
    }


# ------------------------------------------------------------------------------
# 4. Multiple plausible candidates
# ------------------------------------------------------------------------------
def get_multiple_candidates_fixture() -> Dict[str, Any]:
    return {
        "case_id": "case_4_multiple_plausible_candidates",
        "description": "General medicine stem matches multiple distinct formulations requiring human disambiguation",
        "is_mock_test_data": True,
        "input": {
            "candidate_name": "Amoxicillin",
            "observed_dosage": "500 mg",
        },
        "expected": {
            "validation_status": "uncertain",
            "requires_human_review": True,
            "min_candidate_count": 2,
        }
    }


# ------------------------------------------------------------------------------
# 5. No match
# ------------------------------------------------------------------------------
def get_no_match_fixture() -> Dict[str, Any]:
    return {
        "case_id": "case_5_no_match",
        "description": "Extracted candidate text has no correspondence in any authoritative reference",
        "is_mock_test_data": True,
        "input": {
            "candidate_name": "XyzNonExistentPharmaceutical123",
            "observed_dosage": "100 mg",
        },
        "expected": {
            "validation_status": "not_validated",
            "requires_human_review": True,
            "matched_count": 0,
        }
    }


# ------------------------------------------------------------------------------
# 6. Uncertain match
# ------------------------------------------------------------------------------
def get_uncertain_match_fixture() -> Dict[str, Any]:
    return {
        "case_id": "case_6_uncertain_match",
        "description": "Truncated or incomplete cursive stroke yields partial match below autonomous threshold",
        "is_mock_test_data": True,
        "input": {
            "candidate_name": "Amox...",
            "observed_dosage": "500 mg",
        },
        "expected": {
            "validation_status": "uncertain",
            "requires_human_review": True,
        }
    }


# ------------------------------------------------------------------------------
# 7. Dosage mismatch without dosage modification
# ------------------------------------------------------------------------------
def get_dosage_mismatch_fixture() -> Dict[str, Any]:
    return {
        "case_id": "case_7_dosage_mismatch_without_modification",
        "description": "Prescription observed dosage differs from reference standard; observed posology must be preserved",
        "is_mock_test_data": True,
        "input": {
            "candidate_name": "Augmentin 625 Duo",
            "observed_dosage": "1000 mg",  # Mismatched against 625 mg standard
        },
        "expected": {
            "medicine_identity_status": "validated",
            "validation_status": "validated",
            "dosage_observation_preserved": True,
            "observed_dosage": "1000 mg",
            "reference_strength": "625 mg",
            "formulation_consistency": "mismatch",
            "requires_human_review": True,
            "dosage_mutated": False,
        }
    }



# ------------------------------------------------------------------------------
# 8. Brand/generic relationship
# ------------------------------------------------------------------------------
def get_brand_generic_relationship_fixture() -> Dict[str, Any]:
    return {
        "case_id": "case_8_brand_generic_relationship",
        "description": "Preserves both commercial brand and generic active molecule without silent substitution",
        "is_mock_test_data": True,
        "input": {
            "candidate_name": "Augmentin",
        },
        "expected": {
            "brand_name": "Augmentin",
            "generic_name": "Amoxicillin (500mg) + Clavulanic Acid (125mg)",
            "substitutive_overwrite_prevented": True,
        }
    }


# ------------------------------------------------------------------------------
# 9. Duplicate reference records
# ------------------------------------------------------------------------------
def get_duplicate_reference_fixture() -> List[Dict[str, Any]]:
    return [
        {
            "reference_id": "REF-TEST-DUP-01",
            "source": "cdsco-approved-drugs",
            "source_version": "2024.1",
            "medicine_name": "Test Drug Duplicate",
            "normalized_name": "test drug duplicate",
            "provenance": MOCK_CDSCO_PROVENANCE.model_dump(),
        },
        {
            "reference_id": "REF-TEST-DUP-01",  # Duplicate ID
            "source": "cdsco-approved-drugs",
            "source_version": "2024.1",
            "medicine_name": "Test Drug Duplicate Copy",
            "normalized_name": "test drug duplicate copy",
            "provenance": MOCK_CDSCO_PROVENANCE.model_dump(),
        }
    ]


# ------------------------------------------------------------------------------
# 10. Missing source provenance
# ------------------------------------------------------------------------------
def get_missing_provenance_fixture() -> Dict[str, Any]:
    return {
        "reference_id": "REF-TEST-NOPROV-01",
        "source": "unauthorized-custom-source",
        "source_version": "1.0",
        "medicine_name": "Unprovenanced Drug",
        "normalized_name": "unprovenanced drug",
        # Missing required 'provenance'
    }


# ------------------------------------------------------------------------------
# 11. Reference source unavailable
# ------------------------------------------------------------------------------
def get_source_unavailable_manifest_fixture() -> Dict[str, Any]:
    return {
        "manifest_version": "1.0.0-test",
        "created_at": "2026-09-27T00:00:00Z",
        "reference_sources": [
            {
                "source_id": "missing-nonexistent-source",
                "file_path": "data/reference/non_existent_reference_file.json",
                "record_count": 0,
                "sha256": "0000000000000000000000000000000000000000000000000000000000000000",
            }
        ]
    }


# ------------------------------------------------------------------------------
# 12. Retrieval service failure
# ------------------------------------------------------------------------------
def get_retrieval_failure_scenario_fixture() -> Dict[str, Any]:
    return {
        "case_id": "case_12_retrieval_service_failure",
        "description": "Internal retrieval engine failure raises controlled VALIDATION_FAILED exception",
        "is_mock_test_data": True,
        "input": {
            "candidate_name": "Augmentin 625 Duo",
            "simulate_index_crash": True,
        },
        "expected_error_code": "VALIDATION_FAILED",
    }


# ------------------------------------------------------------------------------
# 13. Empty medicine candidate
# ------------------------------------------------------------------------------
def get_empty_candidate_fixture() -> Dict[str, Any]:
    return {
        "case_id": "case_13_empty_medicine_candidate",
        "description": "Empty or blank candidate string handled safely without index queries",
        "is_mock_test_data": True,
        "input": {
            "candidate_name": "   ",
            "observed_dosage": None,
        },
        "expected": {
            "validation_status": "not_validated",
            "requires_human_review": True,
            "evidence_contains": "No medicine name candidate",
        }
    }


# ------------------------------------------------------------------------------
# 14. Multiple medicines in one prescription
# ------------------------------------------------------------------------------
def get_multiple_medicines_prescription_fixture() -> Dict[str, Any]:
    return {
        "case_id": "case_14_multiple_medicines_prescription",
        "description": "Multi-item prescription with distinct active molecules verified independently",
        "is_mock_test_data": True,
        "items": [
            {"candidate_name": "Augmentin 625 Duo", "observed_dosage": "625 mg", "expected_status": "validated"},
            {"candidate_name": "Paracetamol 500mg", "observed_dosage": "500 mg", "expected_status": "validated"},
            {"candidate_name": "Azithromycin 500mg", "observed_dosage": "500 mg", "expected_status": "validated"},
        ]
    }
