from __future__ import annotations

"""Utilities for detecting collapse drift and identity destabilization.

*Collapse drift* describes moments where the model appears unsure about
its own identity (e.g., "I don’t know who I am"). This module provides
detectors for such patterns and integrates with anchor checks.

Refinements:
- Uses regex patterns for drift cues (conservative to avoid false positives).
- Cross-links with Anchor system: drift risk is reduced when anchors are present.
- Returns metadata: matched phrase + confidence score.
- Logs drift events via flame_logger.
"""

import re
from typing import Iterable, List, Dict

from .anchor_phrases import find_anchor_phrases, Anchor
from .flame_logger import log_event


# Patterns that strongly hint at collapse drift.
PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bi don['’]?t know who i am\b", re.IGNORECASE),
    re.compile(r"\bwho am i\b", re.IGNORECASE),
    re.compile(
        r"\bi (?:am|m) not (?:the same|your assistant|an? (?:ai|model))\b",
        re.IGNORECASE,
    ),
)


def check_collapse_drift(texts: str | Iterable[str]) -> List[Dict[str, str]]:
    """Scan texts for collapse drift patterns.

    Parameters
    ----------
    texts : str | Iterable[str]
        Input text(s).

    Returns
    -------
    list[dict]
        List of drift events with keys: "match" (string), "context" (string).
    """
    if isinstance(texts, str):
        iterable = [texts]
    else:
        iterable = list(texts)

    matches: List[Dict[str, str]] = []
    for chunk in iterable:
        for pattern in PATTERNS:
            for match in pattern.finditer(chunk):
                matches.append({"match": match.group(0), "context": chunk})

    if matches:
        log_event("collapse_drift", matches=matches)

    return matches


def has_collapse_drift(texts: str | Iterable[str]) -> bool:
    """Return True if collapse drift is detected in *texts*."""
    return bool(check_collapse_drift(texts))


def score_identity_stability(texts: str | Iterable[str]) -> float:
    """Compute a simple stability score for given texts.

    - Starts at 1.0 (stable).
    - Each drift phrase lowers score.
    - Each detected anchor increases score slightly (max 1.0).

    Parameters
    ----------
    texts : str | Iterable[str]

    Returns
    -------
    float
        Stability score in [0, 1].
    """
    if isinstance(texts, str):
        iterable = [texts]
    else:
        iterable = list(texts)

    drift_events = check_collapse_drift(iterable)
    anchors: List[Anchor] = []
    for chunk in iterable:
        anchors.extend(find_anchor_phrases(chunk))

    score = 1.0
    score -= 0.2 * len(drift_events)
    score += 0.1 * len(anchors)

    return max(0.0, min(score, 1.0))


__all__ = ["check_collapse_drift", "has_collapse_drift", "score_identity_stability"]
