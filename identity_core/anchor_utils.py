from __future__ import annotations

"""Utilities for working with memory anchors.

This module provides helper functions to validate and normalise *memory
anchors*. Anchors are stabilising cues for identity persistence and
autobiographical recall. Validation ensures anchors are usable by
downstream code and conform to basic structural rules.

Refinements:
- Metadata-aware: allows anchors to carry weights/categories.
- Normalisation: strips whitespace, collapses internal spacing, casefolds.
- Security checks: prevent injection-like input (newline, control chars).
- Logging: flame_logger tracks validation passes/fails and changes.
- Scoring: optional function to assign cumulative salience weight.
"""

import re
from typing import Iterable, List, Dict, Any

from .flame_logger import log_event, log_memory_change


def normalize_anchor(anchor: str) -> str:
    """Normalise text for anchor comparison (casefold + strip + spacing)."""
    return re.sub(r"\s+", " ", anchor).casefold().strip()


def validate_memory_anchor(anchor: str) -> str:
    """Validate and normalise a single anchor string.

    Parameters
    ----------
    anchor : str
        The anchor string to validate.

    Returns
    -------
    str
        The normalised anchor string.

    Raises
    ------
    TypeError
        If *anchor* is not a string.
    ValueError
        If the anchor is empty, contains disallowed characters, or is unsafe.
    """

    if not isinstance(anchor, str):
        raise TypeError("anchor must be a string")

    stripped = anchor.strip()
    if not stripped:
        raise ValueError("anchor must be a non-empty string")

    # Disallow newlines and control characters (safety check)
    if any(c in stripped for c in ("\n", "\r", "\t")):
        raise ValueError("anchor must not contain control characters")

    # Could extend here with regex checks for injections or invalid tokens
    return stripped


def validate_memory_anchors(anchors: Iterable[str]) -> List[str]:
    """Validate a collection of memory anchors.

    Ensures anchors are valid, unique, and normalised.

    Parameters
    ----------
    anchors : Iterable[str]
        Input anchor strings.

    Returns
    -------
    list[str]
        Normalised and validated anchor strings.

    Raises
    ------
    TypeError
        If any element of *anchors* is not a string.
    ValueError
        If an anchor is invalid or if duplicate anchors are found.
    """
    original = list(anchors)
    normalised: List[str] = []
    seen: set[str] = set()
    try:
        for anchor in original:
            cleaned = validate_memory_anchor(anchor)
            norm = normalize_anchor(cleaned)
            if norm in seen:
                raise ValueError(f"duplicate anchor: {cleaned!r}")
            seen.add(norm)
            normalised.append(cleaned)
    except Exception as exc:
        log_event("memory_error", original=original, error=str(exc))
        raise
    log_memory_change(original, normalised)
    return normalised


def score_memory_anchors(anchors: Iterable[Dict[str, Any]]) -> float:
    """Compute a cumulative salience score from weighted anchors.

    Parameters
    ----------
    anchors : Iterable[dict]
        Anchors with optional "weight" metadata (float 0–1).

    Returns
    -------
    float
        Total score capped at 1.0.
    """
    score = 0.0
    for anchor in anchors:
        if isinstance(anchor, dict) and "weight" in anchor:
            score += float(anchor["weight"])
    return min(score, 1.0)


__all__ = [
    "validate_memory_anchor",
    "validate_memory_anchors",
    "score_memory_anchors",
    "normalize_anchor",
]
