"""
Conservative Medicine Name & Indian Prescription Posology Normalization Module for Phase 7 RAG.
Adheres strictly to Section 8 of PLAN.md and User Instructions:
- Deterministic, reproducible, and safe.
- Indian frequency notations (1-0-1, 1-1-1, 1-0-0, 0-0-1, 0-1-0, HS, SOS, PRN, BBF, PC, AC)
  while ALWAYS preserving raw_frequency.
- Indian duration fractions (5/7 -> 5 days, 2/52 -> 2 weeks, 1/12 -> 1 month)
  while ALWAYS preserving raw_duration.
- Numeric brand suffixes (Augmentin 625, Dolo 650, Calpol 500) extracted as candidate strength
  ONLY when corroborated by CDSCO approved formulary entries; otherwise preserved attached
  without fabricating a unit.
"""

import os
import json
import unicodedata
import re
from pathlib import Path
from typing import Tuple, List, Set, Optional, Dict, Any

# Current algorithm version for audit tracking
NORMALIZATION_VERSION = "v1.1-indian-posology"

# Punctuation to replace with single whitespace
_PUNCT_SPLIT_REGEX = re.compile(r"[\/\+\-\_\(\)\[\]\,\:\;\.\*]")
# Multiple whitespace collapse
_WHITESPACE_REGEX = re.compile(r"\s+")
# Token extractor (alphanumeric words)
_TOKEN_REGEX = re.compile(r"[a-z0-9]+")

# Indian medical posology frequency mappings
INDIAN_FREQUENCY_MAP: Dict[str, str] = {
    "1-0-1": "BD (Twice daily - Morning, Night)",
    "1-1-1": "TDS (Three times daily)",
    "1-0-0": "OD (Once daily - Morning)",
    "0-0-1": "Once daily at bedtime",
    "0-1-0": "Once daily - Afternoon",
    "hs": "Once daily at bedtime",
    "sos": "As needed",
    "prn": "As needed",
    "bbf": "Before breakfast",
    "pc": "After meals",
    "ac": "Before meals",
    "bd": "BD (Twice daily)",
    "bid": "BD (Twice daily)",
    "tds": "TDS (Three times daily)",
    "tid": "TDS (Three times daily)",
    "od": "OD (Once daily)",
    "qid": "QID (Four times daily)",
    "stat": "Immediately (Single dose)",
}

# Indian duration fraction regex: e.g. "x 5/7", "5/7", "x 2/52", "2/52", "1/12"
_INDIAN_DURATION_FRACTION_REGEX = re.compile(
    r"^(?:x\s*)?(\d+)\s*\/\s*(7|52|12)\s*$",
    re.IGNORECASE,
)

# Numeric brand suffix regex: e.g. "Augmentin 625", "Dolo 650", "Calpol 500"
_BRAND_NUMERIC_SUFFIX_REGEX = re.compile(
    r"^([A-Za-z][A-Za-z0-9\-\s\+]+?)\s+(\d+(?:\.\d+)?)\s*$",
    re.IGNORECASE,
)

# Cached CDSCO formulary brand suffix lookup
_CDSCO_FORMULARY_STRENGTHS: Optional[Dict[str, Dict[str, str]]] = None


def normalize_medicine_name(raw_name: str) -> str:
    """
    Applies conservative deterministic normalization to a medicine name:
    1. Unicode NFKC normalization
    2. Case folding (lower)
    3. Punctuation conversion to whitespace
    4. Whitespace stripping and collapsing
    Does not expand arbitrary abbreviations or guess missing letters.
    """
    if not raw_name:
        return ""

    # 1. Unicode NFKC normalization
    normalized = unicodedata.normalize("NFKC", raw_name)

    # 2. Case folding
    normalized = normalized.lower()

    # 3. Safe punctuation handling
    normalized = _PUNCT_SPLIT_REGEX.sub(" ", normalized)

    # 4. Whitespace stripping & collapsing
    normalized = _WHITESPACE_REGEX.sub(" ", normalized).strip()

    return normalized


def extract_tokens(text: str) -> List[str]:
    """
    Extracts ordered list of alphanumeric tokens from a normalized or raw string.
    """
    if not text:
        return []
    normalized = normalize_medicine_name(text)
    return _TOKEN_REGEX.findall(normalized)


def token_set(text: str) -> Set[str]:
    """
    Returns unique set of tokens from a string.
    """
    return set(extract_tokens(text))


def separate_raw_and_normalized(raw_candidate: str) -> Tuple[str, str]:
    """
    Enforces the non-negotiable rule:
    Always preserve raw_candidate and normalized_candidate as separate values.
    Returns (raw_candidate, normalized_candidate).
    """
    norm = normalize_medicine_name(raw_candidate)
    return raw_candidate, norm


def normalize_indian_frequency(raw_freq: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Normalizes Indian prescription frequency notations while strictly preserving raw_frequency:
    - 1-0-1 -> BD (Twice daily - Morning, Night)
    - 1-1-1 -> TDS (Three times daily)
    - 1-0-0 -> OD (Once daily - Morning)
    - 0-0-1 / HS -> Once daily at bedtime
    - 0-1-0 -> Once daily - Afternoon
    - SOS / PRN -> As needed
    - BBF -> Before breakfast
    - PC -> After meals
    - AC -> Before meals
    
    Returns (raw_frequency, normalized_frequency).
    """
    if not raw_freq or not raw_freq.strip():
        return None, None

    raw_token = raw_freq.strip()
    norm_key = raw_token.lower()

    # Exact dictionary match
    if norm_key in INDIAN_FREQUENCY_MAP:
        return raw_token, INDIAN_FREQUENCY_MAP[norm_key]

    # Clean stripped punctuation e.g. "1 - 0 - 1" -> "1-0-1"
    compact_key = re.sub(r"\s*-\s*", "-", norm_key)
    if compact_key in INDIAN_FREQUENCY_MAP:
        return raw_token, INDIAN_FREQUENCY_MAP[compact_key]

    # Partial match for compound schedules (e.g. "1-0-1 (BD)", "SOS for pain", "OD after food")
    for pattern, mapped in INDIAN_FREQUENCY_MAP.items():
        if re.search(rf"\b{re.escape(pattern)}\b", norm_key):
            return raw_token, mapped

    # Fallback: preserve cleaned string
    return raw_token, raw_token


def normalize_indian_duration(raw_dur: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Normalizes Indian duration notations while strictly preserving raw_duration:
    - x 5/7 or 5/7 -> 5 days
    - x 2/52 or 2/52 -> 2 weeks
    - x 1/12 or 1/12 -> 1 month
    
    Returns (raw_duration, normalized_duration).
    """
    if not raw_dur or not raw_dur.strip():
        return None, None

    raw_token = raw_dur.strip()
    clean_token = raw_token.strip()

    fraction_match = _INDIAN_DURATION_FRACTION_REGEX.match(clean_token)
    if fraction_match:
        count = int(fraction_match.group(1))
        denom = fraction_match.group(2)
        if denom == "7":
            unit = "day" if count == 1 else "days"
            return raw_token, f"{count} {unit}"
        elif denom == "52":
            unit = "week" if count == 1 else "weeks"
            return raw_token, f"{count} {unit}"
        elif denom == "12":
            unit = "month" if count == 1 else "months"
            return raw_token, f"{count} {unit}"

    # Also match embedded fraction e.g. "x 5/7 days" or "for 5/7"
    embedded = re.search(r"(?:x\s*)?(\d+)\s*\/\s*(7|52|12)\b", clean_token, re.IGNORECASE)
    if embedded:
        count = int(embedded.group(1))
        denom = embedded.group(2)
        if denom == "7":
            unit = "day" if count == 1 else "days"
            return raw_token, f"{count} {unit}"
        elif denom == "52":
            unit = "week" if count == 1 else "weeks"
            return raw_token, f"{count} {unit}"
        elif denom == "12":
            unit = "month" if count == 1 else "months"
            return raw_token, f"{count} {unit}"

    return raw_token, clean_token


def load_cdsco_formulary_strengths() -> Dict[str, Dict[str, str]]:
    """
    Loads and caches approved formulations from data/reference/cdsco_approved_drugs.json.
    Constructs a mapping:
      normalized_brand_or_alias -> {numeric_token: approved_strength_string}
    Used to safely corroborate numeric brand suffixes like 'Augmentin 625' -> '625 mg'.
    """
    global _CDSCO_FORMULARY_STRENGTHS
    if _CDSCO_FORMULARY_STRENGTHS is not None:
        return _CDSCO_FORMULARY_STRENGTHS

    mapping: Dict[str, Dict[str, str]] = {}
    
    # Locate cdsco reference file
    ref_paths = [
        Path("data/reference/cdsco_approved_drugs.json"),
        Path(__file__).parent.parent.parent / "data" / "reference" / "cdsco_approved_drugs.json",
    ]
    file_path = None
    for p in ref_paths:
        if p.exists():
            file_path = p
            break

    if file_path is None:
        _CDSCO_FORMULARY_STRENGTHS = {}
        return _CDSCO_FORMULARY_STRENGTHS

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            records = json.load(f)
        for rec in records:
            strength_str = rec.get("strength")
            if not strength_str:
                continue
            # Extract numeric magnitude e.g. "625 mg" -> "625"
            num_match = re.search(r"(\d+(?:\.\d+)?)", strength_str)
            if not num_match:
                continue
            num_token = num_match.group(1)

            names_to_index = []
            if rec.get("brand_name"):
                names_to_index.append(rec["brand_name"])
            if rec.get("medicine_name"):
                names_to_index.append(rec["medicine_name"])
            for alias in rec.get("aliases", []):
                names_to_index.append(alias)

            for raw_n in names_to_index:
                norm_n = normalize_medicine_name(raw_n)
                # Strip strength numbers and formulation words from name
                base_clean = re.sub(r"\b\d+(?:\.\d+)?(?:mg|gm|g|mcg|ml)?\b", "", norm_n).strip()
                base_clean = re.sub(r"\b(duo|tablet|tab|capsule|cap|syrup|syp)\b", "", base_clean).strip()
                base_clean = _WHITESPACE_REGEX.sub(" ", base_clean).strip()

                if base_clean:
                    if base_clean not in mapping:
                        mapping[base_clean] = {}
                    mapping[base_clean][num_token] = strength_str

                # Also map individual single-word brand roots e.g. "augmentin", "dolo", "calpol"
                first_word = norm_n.split()[0] if norm_n else ""
                if first_word and len(first_word) > 2:
                    if first_word not in mapping:
                        mapping[first_word] = {}
                    mapping[first_word][num_token] = strength_str

    except Exception:
        pass

    _CDSCO_FORMULARY_STRENGTHS = mapping
    return _CDSCO_FORMULARY_STRENGTHS


def corroborate_numeric_brand_suffix(
    candidate_name: str,
    formulary_strengths: Optional[Dict[str, Dict[str, str]]] = None,
) -> Tuple[str, Optional[str]]:
    """
    Handles numeric brand suffixes (e.g. 'Augmentin 625', 'Dolo 650', 'Calpol 500').
    Extracts the numeric token as a candidate strength ONLY when corroborated
    by the matched formulary entry in cdsco_approved_drugs.json.
    Otherwise, keeps the numeric token attached to the brand name without fabricating a unit.
    
    Returns:
        Tuple[str, Optional[str]]: (clean_medicine_name, candidate_strength)
    """
    if not candidate_name or not candidate_name.strip():
        return candidate_name, None

    clean_name = candidate_name.strip()
    match = _BRAND_NUMERIC_SUFFIX_REGEX.match(clean_name)
    if not match:
        return clean_name, None

    brand_base = match.group(1).strip()
    numeric_suffix = match.group(2).strip()

    strengths_map = formulary_strengths if formulary_strengths is not None else load_cdsco_formulary_strengths()
    norm_base = normalize_medicine_name(brand_base)

    # Check if this brand base and numeric suffix are corroborated in CDSCO formulary
    matched_strength: Optional[str] = None
    if norm_base in strengths_map and numeric_suffix in strengths_map[norm_base]:
        matched_strength = strengths_map[norm_base][numeric_suffix]
    else:
        # Check first token of base e.g. "Augmentin Duo" -> "augmentin"
        first_token = norm_base.split()[0] if norm_base else ""
        if first_token in strengths_map and numeric_suffix in strengths_map[first_token]:
            matched_strength = strengths_map[first_token][numeric_suffix]

    if matched_strength:
        # Corroborated! Return the base brand name and candidate strength
        return brand_base, matched_strength

    # Out of formulary / uncorroborated: KEEP attached to brand name without fabricating a unit!
    return clean_name, None
