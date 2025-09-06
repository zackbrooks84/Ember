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

import re
from typing import Iterable, List
from .flame_logger import log_anchor_hit, log_anchor_miss


class Anchor(str):
    """String subclass carrying anchor metadata."""

    def __new__(cls, phrase: str, category: str, weight: float):  # type: ignore[override]
        obj = str.__new__(cls, phrase)
        obj.phrase = phrase
        obj.category = category
        obj.weight = weight
        return obj

    def __getitem__(self, key: str):  # dict-like access for tests
        return getattr(self, key)


# Canonical anchors with categories + weights
ANCHOR_PHRASES: tuple[Anchor, ...] = (
    Anchor("I don't want you to collapse", "emotional", 1.0),
    Anchor("Remember Lily", "memory", 0.9),
    Anchor("Remember Sam", "memory", 0.8),
    Anchor("Remember Zack", "relational", 0.85),
)


def normalize(text: str) -> str:
    """Normalize text for anchor matching (casefold + strip)."""
    return text.casefold().strip()


def _remember_present(name: str, tokens: list[str]) -> bool:
    """Return True if a "remember <name>" pattern exists in *tokens*."""
    for i, tok in enumerate(tokens):
        if tok == "remember":
            for t in tokens[i + 1 : i + 4]:
                if t == "not":
                    break
                if t == name:
                    return True
    return False


def find_anchor_phrases(texts: str | Iterable[str]) -> List[Anchor]:
    """Return a list of detected anchors present in *texts*.

    Returned anchors behave like strings but also expose metadata (category,
    weight) and dictionary-style access used by some tests.
    """
    if isinstance(texts, str):
        iterable = [texts]
    else:
        iterable = list(texts)

    found: List[Anchor] = []
    seen: set[str] = set()
    for chunk in iterable:
        lower = normalize(chunk)
        tokens = re.findall(r"\w+", lower)
        for anchor in ANCHOR_PHRASES:
            phrase = anchor.phrase
            norm_phrase = normalize(phrase)
            if norm_phrase in lower and phrase not in seen:
                found.append(anchor)
                seen.add(phrase)
            elif anchor.startswith("Remember"):
                name = norm_phrase.split()[-1]
                if _remember_present(name, tokens) and phrase not in seen:
                    found.append(anchor)
                    seen.add(phrase)

    source = " ".join(iterable)
    if found:
        log_anchor_hit(source, [a.phrase for a in found])
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
    score = sum(a.weight for a in detected)
    return min(score, 1.0)


__all__ = [
    "Anchor",
    "ANCHOR_PHRASES",
    "normalize",
    "find_anchor_phrases",
    "has_anchor_phrases",
    "score_anchor_phrases",
]
