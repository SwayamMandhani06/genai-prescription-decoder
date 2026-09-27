"""
Conservative Medicine Name Normalization Module for Phase 7 RAG.
Adheres strictly to Section 8 of PLAN.md and User Instructions.
Deterministic, reproducible, and safe. Never hallucinates characters or mutates raw candidates.
"""

import unicodedata
import re
from typing import Tuple, List, Set

# Current algorithm version for audit tracking
NORMALIZATION_VERSION = "v1.0-conservative"

# Punctuation to replace with single whitespace
_PUNCT_SPLIT_REGEX = re.compile(r"[\/\+\-\_\(\)\[\]\,\:\;\.\*]")
# Multiple whitespace collapse
_WHITESPACE_REGEX = re.compile(r"\s+")
# Token extractor (alphanumeric words)
_TOKEN_REGEX = re.compile(r"[a-z0-9]+")


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
