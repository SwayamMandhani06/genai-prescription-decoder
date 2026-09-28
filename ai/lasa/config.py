"""
Phase 10: LASA (Look-Alike / Sound-Alike) Detection Configuration.
Configurable thresholds, scoring weights, and curated Tall Man Lettering pairs.
Deterministic, auditable, and safety-oriented.
"""

from typing import Dict, List, Tuple, Optional, Any
from pydantic import BaseModel, Field
import hashlib
import json

# ==============================================================================
# Known ISMP / High-Risk Tall Man Lettering Pairs
# Reference: ISMP List of Look-Alike Drug Name Sets with Recommended Tall Man Letters (2024)
# These are curated look-alike/sound-alike pairs known to cause dispensing errors.
# ==============================================================================

ISMP_PROVENANCE_METADATA: Dict[str, Any] = {
    "source_organization": "Institute for Safe Medication Practices (ISMP), an ECRI affiliate",
    "source_title": "ISMP’s List of Look-Alike Drug Names with Recommended Tall Man Letters",
    "source_version_date": "2024",
    "source_url": "https://www.ismp.org/recommendations/tall-man-letters-list",
    "finite_subset_count": 20,
    "selection_method": (
        "Curated finite 20-pair subset of high-frequency look-alike/sound-alike drug names "
        "commonly cited in pharmacovigilance and dispensing-safety literature, selected as a "
        "deterministic demonstration and development fixture."
    ),
    "is_comprehensive": False,
    "comprehensiveness_statement": (
        "The 20-pair subset is a finite development and demonstration fixture and is NOT comprehensive. "
        "It does not represent all look-alike or sound-alike medicines and cannot be used as an "
        "exhaustive clinical decision-support database or clinical risk assessment tool."
    ),
    "usage_and_license_restrictions": (
        "ISMP Tall Man Lettering recommendations are published by the Institute for Safe Medication "
        "Practices for voluntary educational and patient-safety adoption. Copyright belongs to ISMP. "
        "This implementation uses a finite subset strictly for academic research, education, and development."
    ),
}

TALL_MAN_PAIRS: List[Tuple[str, str, str, str]] = [
    # (drug_a_lower, drug_b_lower, tall_man_a, tall_man_b)
    ("metformin", "metronidazole", "metFORMIN", "metRONIDAZOLE"),
    ("prednisolone", "prednisone", "prednisoLONE", "predniSONE"),
    ("hydroxyzine", "hydralazine", "hydrOXYzine", "hydrALAZINE"),
    ("chlorpromazine", "chlorpropamide", "chlorproMAZINE", "chlorproPAMIDE"),
    ("glipizide", "glyburide", "glipiZIDE", "glyBURIDE"),
    ("clonidine", "clonazepam", "cloNIDine", "cloNAZEpam"),
    ("vinblastine", "vincristine", "vinBLAStine", "vinCRIStine"),
    ("daunorubicin", "doxorubicin", "DAUNOrubicin", "DOXOrubicin"),
    ("cephalexin", "cefazolin", "cephALEXin", "ceFAZolin"),
    ("amitriptyline", "nortriptyline", "amiTRIPtyline", "norTRIPtyline"),
    ("dopamine", "dobutamine", "DOPamine", "DOBUTamine"),
    ("epinephrine", "norepinephrine", "EPINEPHrine", "norEPINEPHrine"),
    ("sulfadiazine", "sulfasalazine", "sulfADIAZINE", "sulfASALAZINE"),
    ("acetazolamide", "acetohexamide", "acetaZOLAMIDE", "acetoHEXAMIDE"),
    ("tolazamide", "tolbutamide", "TOLAZamide", "TOLBUTamide"),
    ("carbamazepine", "oxcarbazepine", "carBAMazepine", "OXcarbazepine"),
    ("cefotaxime", "ceftriaxone", "cefOTAXime", "cefTRIAXone"),
    ("clomiphene", "clomipramine", "clomiPHENE", "clomiPRAMINE"),
    ("cycloserine", "cyclosporine", "cycloSERINE", "cycleSPORINE"),
    ("dimenhydrinate", "diphenhydramine", "dimenHYDRINATE", "diphenHYDRAMINE"),
]


class LasaConfig(BaseModel):
    """
    Phase 10 LASA Detection Configuration.
    All thresholds are explicitly documented and reproducible.
    """
    # --- Similarity Thresholds ---
    orthographic_threshold: float = Field(
        0.70,
        ge=0.0, le=1.0,
        description="Minimum SequenceMatcher ratio for orthographic (lexical) similarity to flag [0.0-1.0]",
    )
    phonetic_threshold: float = Field(
        0.75,
        ge=0.0, le=1.0,
        description="Minimum phonetic similarity ratio to flag [0.0-1.0]",
    )
    combined_threshold: float = Field(
        0.65,
        ge=0.0, le=1.0,
        description="Minimum weighted combined similarity to generate a LASA flag [0.0-1.0]",
    )

    # --- Scoring Weights ---
    orthographic_weight: float = Field(
        0.50,
        ge=0.0, le=1.0,
        description="Weight for orthographic similarity in combined score",
    )
    phonetic_weight: float = Field(
        0.50,
        ge=0.0, le=1.0,
        description="Weight for phonetic similarity in combined score",
    )

    # --- Similarity Conflict Severity Classification Thresholds ---
    # NOTE: Represents name similarity/collision severity, NOT clinical risk.
    high_risk_threshold: float = Field(
        0.85,
        ge=0.0, le=1.0,
        description="Combined similarity >= this classifies conflict severity as 'high' (similarity severity, not clinical risk)",
    )
    medium_risk_threshold: float = Field(
        0.70,
        ge=0.0, le=1.0,
        description="Combined similarity >= this (and < high_risk_threshold) classifies conflict severity as 'medium'",
    )
    # Below medium_risk_threshold = 'low' similarity conflict severity

    # --- Known Pairs Override ---
    known_pair_risk_override: str = Field(
        "high",
        description="If a candidate matches a known ISMP Tall Man pair, override conflict severity to this level",
    )

    # --- Candidate Scope ---
    max_confusable_candidates: int = Field(
        5,
        ge=1, le=20,
        description="Maximum number of confusable counterparts to return per medicine",
    )

    # --- Policy Version ---
    policy_version: str = Field(
        "lasa_policy_v1",
        description="LASA detection policy version identifier",
    )

    @property
    def ismp_provenance(self) -> Dict[str, Any]:
        """Audit provenance metadata for curated ISMP Tall Man pairs."""
        return ISMP_PROVENANCE_METADATA

    def config_hash(self) -> str:
        """Deterministic SHA-256 fingerprint of the active LASA configuration."""
        payload = self.model_dump(mode="json")
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()


_default_config: Optional[LasaConfig] = None


def get_default_lasa_config() -> LasaConfig:
    """Returns the default singleton LasaConfig."""
    global _default_config
    if _default_config is None:
        _default_config = LasaConfig()
    return _default_config
