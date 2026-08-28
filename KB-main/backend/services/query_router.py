"""
Query router — classifies queries to tune hybrid search weights.
"""
import re
from typing import Literal

QueryType = Literal["conceptual", "specific"]

# Error codes, incident IDs, version numbers, quoted phrases
_SPECIFIC_PATTERNS = [
    re.compile(r"\b(?:error|code|incident)\s*#?\s*\d{3,5}\b", re.I),
    re.compile(r"\bINC-\d+\b", re.I),
    re.compile(r"\b\d{3,5}\b"),  # standalone numeric codes like 5023
    re.compile(r"\bv?\d+\.\d+(?:\.\d+)?\b"),  # version numbers
    re.compile(r'"[^"]+"'),  # quoted exact phrase
    re.compile(r"\btech\s*stack\b", re.I),
]

# Acronyms in ALL CAPS (exclude common policy terms asked conceptually)
_ACRONYM_RE = re.compile(r"\b[A-Z]{2,6}\b")
_COMMON_ACRONYMS = frozenset({"PTO", "HR", "IT", "FAQ", "CEO", "VP", "OKR", "EEO"})


def classify_query(query: str) -> QueryType:
    """
    Classify query as conceptual (broad) or specific (exact terms/codes).

    Specific queries get higher BM25 weight in hybrid fusion.
    """
    q = query.strip()
    if not q:
        return "conceptual"

    for pattern in _SPECIFIC_PATTERNS:
        if pattern.search(q):
            return "specific"

    for match in _ACRONYM_RE.finditer(q):
        if match.group() not in _COMMON_ACRONYMS:
            return "specific"

    # Short keyword-heavy queries
    words = q.split()
    if len(words) <= 5 and any(
        w.lower() in ("stack", "api", "inc", "error", "5023", "salesforce", "postgresql")
        for w in words
    ):
        return "specific"

    return "conceptual"


def alpha_for_query_type(query_type: QueryType) -> float:
    """Vector weight (alpha); remainder goes to BM25."""
    if query_type == "specific":
        return 0.48
    return 0.68
