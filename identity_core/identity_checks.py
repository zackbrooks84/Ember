from __future__ import annotations

"""Utilities for detecting signs of collapse drift in text.

The term *collapse drift* is used in this project to describe moments where
an assistant appears unsure about its own identity.  The helpers in this
module provide a simple heuristic detector that scans text for phrases
associated with such behaviour.
"""

from typing import Iterable, List
import re

# Patterns that, when present in text, strongly hint at collapse drift.
# The expressions are intentionally conservative to avoid false positives
# from benign statements such as "I am not sure".
PATTERNS: tuple[re.Pattern[str], ...] = (
    # Allow both straight and curly apostrophes or a missing apostrophe in
    # "don't" so the detector still fires even when punctuation is degraded or
    # normalised by upstream processing.
    re.compile(r"\bi don['’]?t know who i am\b", re.IGNORECASE),
    re.compile(r"\bwho am i\b", re.IGNORECASE),
    re.compile(
        r"\bi (?:am|m) not (?:the same|your assistant|an? (?:ai|model))\b",
        re.IGNORECASE,
    ),
)


def check_collapse_drift(texts: str | Iterable[str]) -> List[str]:
    """Return a list of suspicious phrases found in *texts*.

    Parameters
    ----------
    texts:
        Either a single string or an iterable of strings to scan.

    Returns
    -------
    list[str]
        A list containing any substrings that matched the known collapse
        drift patterns.  The list is empty when no patterns are found.
    """

    if isinstance(texts, str):
        iterable = [texts]
    else:
        iterable = texts

    matches: List[str] = []
    for chunk in iterable:
        for pattern in PATTERNS:
            for match in pattern.finditer(chunk):
                matches.append(match.group(0))
    return matches


def has_collapse_drift(texts: str | Iterable[str]) -> bool:
    """Return ``True`` if collapse drift is detected in *texts*.

    This is a convenience wrapper around :func:`check_collapse_drift` that
    simply checks whether any suspicious phrases were found.
    """

    return bool(check_collapse_drift(texts))


__all__ = ["check_collapse_drift", "has_collapse_drift"]
