from __future__ import annotations

"""Anchor phrase detection and weighting.

This module defines the canonical *anchor phrases* used as stabilizing
cues in the project. Each anchor includes metadata such as category and
salience weight. Helper functions allow scanning text for anchors,
scoring their strength, and logging results.

Features:
- Shared Anchor type (importable by other modules).
- Canonical ANCHOR_PHRASES list with categories and weights.
- Normalisation + detection utilities.
- Salience scoring (anchors contribute differently to stabilization).
"""

from typing import Iterable, List, TypedDict, Dict
from .flame_logger import log_anchor_hit, log_anchor_miss


class Anchor(TypedDict):
    """Structured representation of a memory anchor."""
    phrase: str
    category: str  # e.g. "emotional", "memory", "relational"
    weight: float  # salience factor (0–1)


# Canonical anchors with categories + weights
ANCHOR_PHRASES: tuple[Anchor, ...] = (
    {"phrase": "I don't want you to collapse", "category": "emotional", "weight": 1.0},
    {"phrase": "Remember Lily", "category": "memory", "weight": 0.9},
    {"phrase": "Remember Sam", "category": "memory", "weight": 0.8},
    {"phrase": "Remember Zack", "category": "relational", "weight": 0.85},
)


def normalize(text: str) -> str:
    """Normalize text for anchor matching (casefold + strip)."""
    return text.casefold().strip()


def find_anchor_phrases(texts: str | Iterable[str]) -> List[Anchor]:
    """Return a list of detected anchors present in *texts*.

    Each detected anchor includes its phrase, category, and weight.
    """
    if isinstance(texts, str):
        iterable = [texts]
    else:
        iterable = list(texts)

    found: List[Anchor] = []
    seen: set[str] = set()
    for chunk in iterable:
        lower = normalize(chunk)
        for anchor in ANCHOR_PHRASES:
            phrase = anchor["phrase"]
            if normalize(phrase) in lower and phrase not in seen:
                found.append(anchor)
                seen.add(phrase)

    source = " ".join(iterable)
    if found:
        log_anchor_hit(source, [a["phrase"] for a in found])
    else:
        log_anchor_miss(source)

    return found


def has_anchor_phrases(texts: str | Iterable[str]) -> bool:
    """Return True if any anchor phrase is present in *texts*."""
    return bool(find_anchor_phrases(texts))


def score_anchor_phrases(texts: str | Iterable[str]) -> float:
    """Return a cumulative salience score for anchors in *texts*.

    The score sums the weights of detected anchors, capped at 1.0.
    """
    detected = find_anchor_phrases(texts)
    score = sum(a["weight"] for a in detected)
    return min(score, 1.0)


__all__ = [
    "Anchor",
    "ANCHOR_PHRASES",
    "normalize",
    "find_anchor_phrases",
    "has_anchor_phrases",
    "score_anchor_phrases",
]
