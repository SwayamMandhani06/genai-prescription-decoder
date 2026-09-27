"""
Deterministic Normalization Engine (Phase 3)
Provides reversible, transparent text, dosage, and frequency normalization
while strictly preserving clinical distinctions (e.g. 1.0 mg vs 10 mg safety).
"""

import re
import unicodedata
from typing import Optional, Tuple, Dict, Any
from pydantic import BaseModel, Field


class NormalizedDosageResult(BaseModel):
    """Result of dosage normalization preserving original token."""
    raw_token: str
    numeric_value: Optional[float] = None
    unit: Optional[str] = None
    canonical_string: str
    is_valid: bool = True


class NormalizedFrequencyResult(BaseModel):
    """Result of frequency normalization preserving original token."""
    raw_token: str
    canonical_code: Optional[str] = None  # Standard code (e.g. 'BD', 'TDS', 'OD')
    standard_expansion: Optional[str] = None  # Human-readable expansion (e.g. 'Twice daily')
    daily_count: Optional[int] = None
    is_valid: bool = True


def normalize_text(text: str) -> str:
    """
    Applies deterministic Unicode normalization (NFKC) and controlled whitespace collapsing.
    Preserves hyphens, decimals, and slashes essential for medical posology.
    """
    if not text:
        return ""
    # Unicode NFKC normalization decomposes compatibility forms and recomposes canon
    normalized = unicodedata.normalize("NFKC", text)
    # Replace non-breaking spaces and tabs with standard space
    normalized = re.sub(r"[\r\n\t\u00a0\u2000-\u200b]+", " ", normalized)
    # Collapse multiple spaces
    normalized = re.sub(r" +", " ", normalized)
    return normalized.strip()


DOSAGE_UNIT_MAP: Dict[str, str] = {
    "mg": "mg",
    "mgs": "mg",
    "milligram": "mg",
    "milligrams": "mg",
    "mcg": "mcg",
    "ug": "mcg",
    "microgram": "mcg",
    "micrograms": "mcg",
    "g": "g",
    "gm": "g",
    "gms": "g",
    "gram": "g",
    "grams": "g",
    "ml": "ml",
    "mls": "ml",
    "milliliter": "ml",
    "milliliters": "ml",
    "tab": "tab",
    "tabs": "tab",
    "tablet": "tab",
    "tablets": "tab",
    "cap": "cap",
    "caps": "cap",
    "capsule": "cap",
    "capsules": "cap",
    "puff": "puffs",
    "puffs": "puffs",
    "drop": "drops",
    "drops": "drops",
    "iu": "IU",
    "units": "IU",
}


def normalize_dosage(raw_dosage: Optional[str]) -> NormalizedDosageResult:
    """
    Normalizes dosage representation.
    SAFETY CRITICAL: Preserves exact decimal precision (e.g. '0.5 mg' or '1.0 mg').
    Does not convert floats to integers or strip decimal zeros blindly.
    """
    if not raw_dosage or not raw_dosage.strip():
        return NormalizedDosageResult(raw_token="", canonical_string="")

    clean = normalize_text(raw_dosage).lower()
    
    # Match pattern: number followed by unit (e.g. '625 mg', '0.5ml', '500-mg')
    match = re.search(r"(\d+(?:\.\d+)?)\s*([a-zA-Z]+)", clean)
    if not match:
        # Fallback for plain tokens
        return NormalizedDosageResult(raw_token=raw_dosage, canonical_string=normalize_text(raw_dosage))

    num_str, unit_raw = match.group(1), match.group(2)
    numeric_val = float(num_str)
    canonical_unit = DOSAGE_UNIT_MAP.get(unit_raw.lower(), unit_raw)

    # Reconstruct canonical representation preserving decimal notation
    canonical = f"{num_str} {canonical_unit}"

    return NormalizedDosageResult(
        raw_token=raw_dosage,
        numeric_value=numeric_val,
        unit=canonical_unit,
        canonical_string=canonical,
        is_valid=True,
    )


FREQUENCY_PATTERN_MAP: Dict[str, Tuple[str, str, int]] = {
    # Code, Expansion, Daily Count
    "1-0-1": ("BD", "Twice daily (Morning, Night)", 2),
    "1-1-1": ("TDS", "Three times daily (Morning, Afternoon, Night)", 3),
    "1-0-0": ("OD", "Once daily (Morning)", 1),
    "0-1-0": ("OD", "Once daily (Afternoon)", 1),
    "0-0-1": ("HS", "Once daily (At bedtime)", 1),
    "1-1-1-1": ("QID", "Four times daily", 4),
    "bd": ("BD", "Twice daily", 2),
    "bid": ("BD", "Twice daily", 2),
    "b.i.d.": ("BD", "Twice daily", 2),
    "twice daily": ("BD", "Twice daily", 2),
    "tds": ("TDS", "Three times daily", 3),
    "tid": ("TDS", "Three times daily", 3),
    "t.i.d.": ("TDS", "Three times daily", 3),
    "three times daily": ("TDS", "Three times daily", 3),
    "od": ("OD", "Once daily", 1),
    "qd": ("OD", "Once daily", 1),
    "q.d.": ("OD", "Once daily", 1),
    "once daily": ("OD", "Once daily", 1),
    "qid": ("QID", "Four times daily", 4),
    "q.i.d.": ("QID", "Four times daily", 4),
    "sos": ("SOS", "As needed / when necessary", 0),
    "prn": ("SOS", "As needed / when necessary", 0),
    "hs": ("HS", "At bedtime", 1),
    "qhs": ("HS", "At bedtime", 1),
}


def normalize_frequency(raw_frequency: Optional[str]) -> NormalizedFrequencyResult:
    """
    Standardizes Latin shorthand and Indian outpatient numeric patterns (e.g. '1-0-1' or 'TDS').
    """
    if not raw_frequency or not raw_frequency.strip():
        return NormalizedFrequencyResult(raw_token="", is_valid=False)

    clean = normalize_text(raw_frequency).lower()
    
    # Strip common punctuation around shorthand
    lookup_key = re.sub(r"[\(\)\[\]]", "", clean).strip()

    if lookup_key in FREQUENCY_PATTERN_MAP:
        code, expansion, count = FREQUENCY_PATTERN_MAP[lookup_key]
        return NormalizedFrequencyResult(
            raw_token=raw_frequency,
            canonical_code=code,
            standard_expansion=expansion,
            daily_count=count,
            is_valid=True,
        )

    # Check for pattern variations (e.g. '1 - 0 - 1')
    pattern_clean = re.sub(r"\s*-\s*", "-", lookup_key)
    if pattern_clean in FREQUENCY_PATTERN_MAP:
        code, expansion, count = FREQUENCY_PATTERN_MAP[pattern_clean]
        return NormalizedFrequencyResult(
            raw_token=raw_frequency,
            canonical_code=code,
            standard_expansion=expansion,
            daily_count=count,
            is_valid=True,
        )

    return NormalizedFrequencyResult(
        raw_token=raw_frequency,
        canonical_code=raw_frequency.strip().upper(),
        standard_expansion=raw_frequency.strip(),
        daily_count=None,
        is_valid=False,
    )


class ClinicalNormalizer:
    """Batch normalization utility over clinical prescription annotations."""

    @staticmethod
    def normalize_entity(
        medicine_name: str,
        dosage_strength: Optional[str] = None,
        frequency: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Returns a normalized representation dictionary while retaining all original inputs."""
        norm_name = normalize_text(medicine_name)
        norm_dose = normalize_dosage(dosage_strength)
        norm_freq = normalize_frequency(frequency)

        return {
            "original_name": medicine_name,
            "normalized_name": norm_name,
            "original_dosage": dosage_strength,
            "dosage": norm_dose.model_dump(),
            "original_frequency": frequency,
            "frequency": norm_freq.model_dump(),
        }
