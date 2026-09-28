"""
Phase 10: Lexical and Phonetic Similarity Engine for LASA Detection.
Implements deterministic, reproducible similarity computations:
- Orthographic similarity via difflib.SequenceMatcher
- Phonetic similarity via Double Metaphone encoding
- Combined weighted scoring
- Known Tall Man pair lookup

Does NOT use opaque vector embeddings or LLM-based similarity.
All computations are deterministic and auditable.
"""

import difflib
import re
from typing import Optional, Tuple, Set

from ai.rag.normalization import normalize_medicine_name
from ai.lasa.config import TALL_MAN_PAIRS

# Common pharmaceutical formulation, dosage, and frequency stopwords
FORMULATION_STOPWORDS = frozenset({
    "sr", "er", "xr", "cr", "pr", "dr", "xl",
    "od", "bd", "tds", "tid", "qid", "hs", "prn", "sos",
    "tab", "tablet", "tablets", "cap", "capsule", "capsules",
    "oral", "syrup", "susp", "suspension", "sol", "solution",
    "inj", "injection", "drops", "ointment", "cream", "gel",
    "mg", "gm", "g", "mcg", "ml", "iu", "units",
    "duo", "forte", "plus", "extra", "regular",
})

_DOSAGE_PATTERN = re.compile(r"^\d+(mg|gm|g|mcg|ml|iu|units)?$")


def extract_base_stem(name: str) -> str:
    """
    Extracts the base pharmaceutical entity stem from a medicine name by stripping
    dosage numbers, units, formulation abbreviations, and common pharmaceutical stop words.
    Used to prevent self-collision between different formulations/dosages of the same drug entity.
    """
    if not name:
        return ""
    normalized = normalize_medicine_name(name)
    tokens = normalized.split()
    kept_tokens = []
    for token in tokens:
        if token.isdigit() or _DOSAGE_PATTERN.match(token) or token in FORMULATION_STOPWORDS:
            continue
        kept_tokens.append(token)
    stem = " ".join(kept_tokens).strip()
    return stem if stem else normalized


# ==============================================================================
# Double Metaphone Implementation (Simplified)
# Phonetic encoding algorithm producing primary and secondary codes.
# Based on Lawrence Philips' algorithm, adapted for pharmaceutical names.
# ==============================================================================

# Vowel set for phonetic processing
_VOWELS = frozenset("AEIOU")

# Consonant mapping for simplified metaphone (pharmaceutical-focused)
_METAPHONE_MAP = {
    "PH": "F",
    "GH": "F",
    "KN": "N",
    "WR": "R",
    "AE": "E",
    "CK": "K",
    "SCH": "SK",
    "SH": "X",
    "TH": "0",
    "CH": "X",
    "QU": "KW",
}

_SIMPLE_CONSONANT_MAP = {
    "B": "P",
    "C": "K",
    "D": "T",
    "F": "F",
    "G": "K",
    "H": "H",
    "J": "J",
    "K": "K",
    "L": "L",
    "M": "M",
    "N": "N",
    "P": "P",
    "Q": "K",
    "R": "R",
    "S": "S",
    "T": "T",
    "V": "F",
    "W": "W",
    "X": "KS",
    "Y": "Y",
    "Z": "S",
}


def _double_metaphone(word: str) -> Tuple[str, str]:
    """
    Produces a simplified Double Metaphone encoding tuple (primary, secondary).
    Optimized for pharmaceutical name comparison rather than general English.
    Returns (primary_code, secondary_code) of up to 6 characters each.
    """
    if not word:
        return ("", "")

    word = word.upper().strip()
    # Remove non-alpha characters
    word = "".join(c for c in word if c.isalpha())
    if not word:
        return ("", "")

    primary = []
    secondary = []
    i = 0
    max_len = 6

    # Skip silent initial consonant clusters
    if word[:2] in ("GN", "KN", "PN", "WR", "AE"):
        i = 1

    while i < len(word) and len(primary) < max_len:
        c = word[i]
        two = word[i:i+2] if i + 1 < len(word) else ""
        three = word[i:i+3] if i + 2 < len(word) else ""

        # Skip duplicate adjacent consonants
        if i > 0 and c == word[i-1] and c not in "CS":
            i += 1
            continue

        # Vowels: only encode if at beginning
        if c in _VOWELS:
            if i == 0:
                primary.append("A")
                secondary.append("A")
            i += 1
            continue

        # Multi-character substitutions
        if three in _METAPHONE_MAP:
            code = _METAPHONE_MAP[three]
            primary.append(code)
            secondary.append(code)
            i += 3
            continue

        if two in _METAPHONE_MAP:
            code = _METAPHONE_MAP[two]
            primary.append(code)
            secondary.append(code)
            i += 2
            continue

        # Special handling for C
        if c == "C":
            if two == "CI" or two == "CE" or two == "CY":
                primary.append("S")
                secondary.append("S")
                i += 2
                continue
            else:
                primary.append("K")
                secondary.append("K")
                i += 1
                continue

        # Special handling for G
        if c == "G":
            if two == "GI" or two == "GE" or two == "GY":
                primary.append("J")
                secondary.append("J")
                i += 2
                continue
            else:
                primary.append("K")
                secondary.append("K")
                i += 1
                continue

        # Simple consonant mapping
        if c in _SIMPLE_CONSONANT_MAP:
            code = _SIMPLE_CONSONANT_MAP[c]
            primary.append(code)
            secondary.append(code)
            i += 1
            continue

        i += 1

    primary_code = "".join(primary)[:max_len]
    secondary_code = "".join(secondary)[:max_len]
    return (primary_code, secondary_code)


def compute_metaphone(name: str) -> Tuple[str, str]:
    """
    Computes Double Metaphone codes for a medicine name.
    Normalizes name before encoding.
    Returns (primary_code, secondary_code).
    """
    normalized = normalize_medicine_name(name)
    # Remove numeric tokens (dosage strengths like 500, 250mg)
    tokens = [t for t in normalized.split() if t.isalpha()]
    combined = "".join(tokens)
    return _double_metaphone(combined)


def orthographic_similarity(name_a: str, name_b: str) -> float:
    """
    Computes orthographic (lexical) similarity between two medicine names
    using difflib.SequenceMatcher on normalized forms.
    Returns ratio in [0.0, 1.0].
    """
    norm_a = normalize_medicine_name(name_a)
    norm_b = normalize_medicine_name(name_b)
    if not norm_a or not norm_b:
        return 0.0
    return difflib.SequenceMatcher(None, norm_a, norm_b).ratio()


def phonetic_similarity(name_a: str, name_b: str) -> float:
    """
    Computes phonetic similarity between two medicine names using Double Metaphone.
    Compares primary codes using SequenceMatcher for graduated scoring.
    Returns ratio in [0.0, 1.0].
    """
    code_a = compute_metaphone(name_a)
    code_b = compute_metaphone(name_b)

    if not code_a[0] or not code_b[0]:
        return 0.0

    # Primary-primary comparison
    primary_ratio = difflib.SequenceMatcher(None, code_a[0], code_b[0]).ratio()

    # Also check primary-secondary cross-matches for broader coverage
    cross_scores = [primary_ratio]
    if code_a[1] and code_b[0]:
        cross_scores.append(difflib.SequenceMatcher(None, code_a[1], code_b[0]).ratio())
    if code_a[0] and code_b[1]:
        cross_scores.append(difflib.SequenceMatcher(None, code_a[0], code_b[1]).ratio())

    return max(cross_scores)


def metaphone_exact_match(name_a: str, name_b: str) -> bool:
    """
    Returns True if the primary Double Metaphone codes of both names are identical.
    """
    code_a = compute_metaphone(name_a)
    code_b = compute_metaphone(name_b)
    if not code_a[0] or not code_b[0]:
        return False
    return code_a[0] == code_b[0]


def lookup_tall_man_pair(name_a: str, name_b: str) -> Optional[Tuple[str, str, str, str]]:
    """
    Checks if two medicine names are a known ISMP Tall Man Lettering pair.
    Returns the pair tuple (drug_a, drug_b, tall_man_a, tall_man_b) if found, None otherwise.
    Comparison is bidirectional and case-insensitive.
    Also handles names with dosage/formulation suffixes by checking base stems.
    """
    norm_a = normalize_medicine_name(name_a)
    norm_b = normalize_medicine_name(name_b)
    stem_a = extract_base_stem(norm_a)
    stem_b = extract_base_stem(norm_b)

    for pair in TALL_MAN_PAIRS:
        pair_a = pair[0]  # already lowercase
        pair_b = pair[1]  # already lowercase
        if (
            (norm_a == pair_a and norm_b == pair_b)
            or (norm_a == pair_b and norm_b == pair_a)
            or (stem_a == pair_a and stem_b == pair_b)
            or (stem_a == pair_b and stem_b == pair_a)
        ):
            # Return in canonical order matching the query
            if norm_a == pair_a or stem_a == pair_a:
                return pair
            else:
                return (pair[1], pair[0], pair[3], pair[2])

    return None


def combined_similarity(
    name_a: str,
    name_b: str,
    ortho_weight: float = 0.5,
    phonetic_weight: float = 0.5,
) -> Tuple[float, float, float, bool]:
    """
    Computes all similarity dimensions and returns:
    (orthographic_score, phonetic_score, combined_score, metaphone_match)
    """
    ortho = orthographic_similarity(name_a, name_b)
    phon = phonetic_similarity(name_a, name_b)
    meta_match = metaphone_exact_match(name_a, name_b)

    combined = (ortho_weight * ortho) + (phonetic_weight * phon)
    return (ortho, phon, combined, meta_match)
