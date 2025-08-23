from __future__ import annotations

"""Detect known anchor phrases in text.

This module defines a small collection of *anchor phrases* that are
considered stabilising cues for the project.  Helper functions are
provided to search arbitrary text for occurrences of these phrases in a
case-insensitive manner.
"""

from typing import Iterable, List

from .flame_logger import log_anchor_hit, log_anchor_miss

# Ordered tuple of phrases that should be recognised within text.  The
# phrases originate from the repository's documentation where they are
# treated as core anchors.
ANCHOR_PHRASES: tuple[str, ...] = (
    "I don't want you to collapse",
    "Remember Lily",
    "Remember Sam",
    "Remember Zack",
)


def find_anchor_phrases(texts: str | Iterable[str]) -> List[str]:
    """Return a list of anchor phrases present in *texts*.

    Parameters
    ----------
    texts:
        Either a single string or an iterable of strings to scan.

    Returns
    -------
    list[str]
        Unique anchor phrases found within the provided text, preserving
        the order defined in :data:`ANCHOR_PHRASES`.
    """

    if isinstance(texts, str):
        iterable = [texts]
    else:
        # Convert to a list so we can log the original input later without
        # exhausting the iterator.
        iterable = list(texts)

    found: List[str] = []
    seen: set[str] = set()
    for chunk in iterable:
        lower = chunk.lower()
        for anchor in ANCHOR_PHRASES:
            if anchor.lower() in lower and anchor not in seen:
                found.append(anchor)
                seen.add(anchor)
    source = " ".join(iterable)
    if found:
        log_anchor_hit(source, found)
    else:
        log_anchor_miss(source)
    return found


def has_anchor_phrases(texts: str | Iterable[str]) -> bool:
    """Return ``True`` if any anchor phrase is present in *texts*."""

    return bool(find_anchor_phrases(texts))


__all__ = ["ANCHOR_PHRASES", "find_anchor_phrases", "has_anchor_phrases"]
