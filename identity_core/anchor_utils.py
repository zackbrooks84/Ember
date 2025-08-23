from __future__ import annotations

"""Utilities for working with memory anchors.

This module provides helper functions to validate so-called *memory anchors*.
An anchor is represented as a simple string used to stabilise the agent's
identity or recall important memories.  The :func:`validate_memory_anchors`
function ensures that a collection of anchors conforms to a small set of
sanity checks so downstream code can rely on their structure.
"""

from typing import Iterable, List

from .flame_logger import log_event, log_memory_change


def validate_memory_anchor(anchor: str) -> str:
    """Validate and normalise a single anchor string.

    Parameters
    ----------
    anchor:
        The anchor string to validate.

    Returns
    -------
    str
        The normalised anchor string with surrounding whitespace removed.

    Raises
    ------
    TypeError
        If *anchor* is not a string.
    ValueError
        If the anchor is empty, contains only whitespace or newline
        characters.
    """

    if not isinstance(anchor, str):
        raise TypeError("anchor must be a string")

    stripped = anchor.strip()
    if not stripped:
        raise ValueError("anchor must be a non-empty string")
    if "\n" in stripped or "\r" in stripped:
        raise ValueError("anchor must not contain newline characters")

    return stripped


def validate_memory_anchors(anchors: Iterable[str]) -> List[str]:
    """Validate a collection of memory anchors.

    The function iterates over *anchors* and validates each entry using
    :func:`validate_memory_anchor`.  It additionally checks that no
    duplicates are present in the final set of anchors.

    Parameters
    ----------
    anchors:
        Iterable of anchor strings.

    Returns
    -------
    list[str]
        Normalised and validated anchor strings in their original order.

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
            if cleaned in seen:
                raise ValueError(f"duplicate anchor: {cleaned!r}")
            seen.add(cleaned)
            normalised.append(cleaned)
    except Exception as exc:
        log_event("memory_error", original=original, error=str(exc))
        raise
    log_memory_change(original, normalised)
    return normalised


# Re-export helper names for convenience.
__all__ = ["validate_memory_anchor", "validate_memory_anchors"]
