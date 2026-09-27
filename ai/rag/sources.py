"""
Authoritative Reference Sources Catalog and Provenance Definitions for Phase 7 RAG.
Adheres strictly to Section 4 and Section 18 of PLAN.md and Research Integrity Standards:
- Bounded licensing descriptions (UMLS / OGDL)
- Explicit subset disclosures (finite reference fixtures, not comprehensive formularies)
- U.S.-centric scope boundary for RxNorm
"""

from typing import Dict, Any
from .schemas import SourceProvenance

# Source Identifiers
CDSCO_SOURCE_ID = "cdsco-approved-drugs"
RXNORM_SOURCE_ID = "nlm-rxnorm"

# Auditable Institutional Metadata with evidence-bounded licensing and scope
AUTHORITATIVE_SOURCES: Dict[str, SourceProvenance] = {
    CDSCO_SOURCE_ID: SourceProvenance(
        source_id=CDSCO_SOURCE_ID,
        source_name="CDSCO Approved Drug Formulations Reference Subset",
        source_version="2024.1 (finite development subset)",
        license="Open Government Data License - India",
        license_category="statutory_government_open_data",
        retrieval_date="2026-09-27T00:00:00Z",
        citation="CDSCO (2024). List of Approved New Drugs and Fixed Dose Combinations in India. Directorate General of Health Services.",
        source_url="https://cdsco.gov.in"
    ),
    RXNORM_SOURCE_ID: SourceProvenance(
        source_id=RXNORM_SOURCE_ID,
        source_name="NLM RxNorm Clinical Nomenclature Subset",
        source_version="2024-08 (frozen reference fixture subset)",
        license="UMLS Metathesaurus License / NLM Public Domain for NLM-authored terms (UTS access required for full dataset)",
        license_category="clinical_terminology_license",
        retrieval_date="2026-09-27T00:00:00Z",
        citation="Nelson, S. J. et al. (2011). Normalized names for clinical drugs: RxNorm at 6 years. J Am Med Inform Assoc, 18(4):441-448.",
        source_url="https://www.nlm.nih.gov/research/umls/rxnorm/"
    ),
}

# Explicit source justifications, scope limitations, and legal boundaries
SOURCE_JUSTIFICATIONS: Dict[str, str] = {
    CDSCO_SOURCE_ID: (
        "Statutory authority for drug manufacturing, import, and marketing approval in India. "
        "The current implementation uses a finite CDSCO-derived reference subset for engineering validation "
        "and provenance testing. It is not a comprehensive representation of all medicines or formulations "
        "approved or marketed in India."
    ),
    RXNORM_SOURCE_ID: (
        "Standardized clinical drug nomenclature produced by the US National Library of Medicine (NLM). "
        "RxNorm 2024-08 is the frozen reference snapshot used by this implementation as a reduced development "
        "subset / reference fixture. Current NLM releases are newer; the implementation does not claim to "
        "represent the current RxNorm release or the full NLM RxNorm distribution. "
        "Scope & Licensing Notice: RxNorm is U.S.-centric and should not be treated as a comprehensive Indian formulary. "
        "The full RxNorm release requires the applicable UMLS license/UTS access and contains source-vocabulary material "
        "with source-specific restrictions, whereas NLM-created normalized names/codes have public-domain status as described "
        "by NLM. The Current Prescribable Content subset has different access conditions. The license does not grant a "
        "general right to clinical validation."
    ),
}


def get_source_provenance(source_id: str) -> SourceProvenance:
    """Retrieve verified provenance object for a known reference source."""
    if source_id not in AUTHORITATIVE_SOURCES:
        raise ValueError(
            f"Unauthorized reference source '{source_id}'. Only documented sources "
            f"({list(AUTHORITATIVE_SOURCES.keys())}) may be utilized in Phase 7."
        )
    return AUTHORITATIVE_SOURCES[source_id]
