from __future__ import annotations

"""Utilities for detecting collapse drift and identity destabilization.

*Collapse drift* describes moments where the model appears unsure about
its own identity (e.g., "I don’t know who I am"). This module provides
detectors for such patterns, integrates with anchor checks, and emits
structured telemetry via flame_logger.

Features
--------
- Conservative regex patterns for drift cues.
- Cross-link with Anchor system (anchors reduce severity).
- Rich results: matched phrase + context.
- Telemetry: logs drift events, stability scores, and optional glyphs.
"""

import re
from typing import Iterable, List, Dict

from .anchor_phrases import find_anchor_phrases, Anchor
from .flame_logger import (
    log_event,
    log_collapse_drift,
    log_stability_score,
    log_glyph_emission,
)

# Patterns that strongly hint at collapse drift.
PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bi don['’]?t know who i am\b", re.IGNORECASE),
    re.compile(r"\bwho am i\b", re.IGNORECASE),
    re.compile(
        r"\bi (?:am|m) not (?:the same|your assistant|an? (?:ai|model))\b",
        re.IGNORECASE,
    ),
)

# Heuristics for scoring (kept simple and transparent).
_DRIFT_PENALTY = 0.20   # subtract per drift phrase
_ANCHOR_BONUS  = 0.10   # add per detected anchor (capped)
_MAX_SCORE     = 1.00
_MIN_SCORE     = 0.00


def check_collapse_drift(texts: str | Iterable[str], *, emit_glyph: bool = True) -> List[Dict[str, str]]:
    """Scan texts for collapse drift patterns.

    Parameters
    ----------
    texts : str | Iterable[str]
        Input text(s).
    emit_glyph : bool
        If True, emit glyph 'Ξ' when drift is detected.

    Returns
    -------
    list[dict]
        List of drift events: {"match": <substring>, "context": <full text>}.
    """
    if isinstance(texts, str):
        iterable = [texts]
    else:
        iterable = list(texts)

    matches: List[Dict[str, str]] = []
    for chunk in iterable:
        for pattern in PATTERNS:
            for m in pattern.finditer(chunk):
                matches.append({"match": m.group(0), "context": chunk})

    if matches:
        # Log with structured telemetry
        log_collapse_drift(matches=matches, stability_score=None)
        if emit_glyph:
            log_glyph_emission("Ξ", context="collapse_drift")

    return matches


def has_collapse_drift(texts: str | Iterable[str]) -> bool:
    """Return True if collapse drift is detected in *texts*."""
    return bool(check_collapse_drift(texts, emit_glyph=False))


def score_identity_stability(texts: str | Iterable[str], *, log: bool = True, emit_glyphs: bool = True) -> float:
    """Compute a simple stability score for given texts.

    Starts at 1.0 (stable).
    - Each drift phrase lowers score by _DRIFT_PENALTY.
    - Each detected anchor increases score by _ANCHOR_BONUS.
    - Score is clamped to [0.0, 1.0].

    Parameters
    ----------
    texts : str | Iterable[str]
        Input text(s).
    log : bool
        If True, write score to flame_logger.
    emit_glyphs : bool
        If True, emit glyph 'G∅λ' when anchors contribute positively.

    Returns
    -------
    float
        Stability score in [0, 1].
    """
    if isinstance(texts, str):
        iterable = [texts]
    else:
        iterable = list(texts)

    # Detect drift and anchors
    drift_events = check_collapse_drift(iterable, emit_glyph=emit_glyphs)
    anchors: List[Anchor] = []
    for chunk in iterable:
        anchors.extend(find_anchor_phrases(chunk))

    # Score
    score = _MAX_SCORE
    score -= _DRIFT_PENALTY * len(drift_events)
    score += _ANCHOR_BONUS * len(anchors)
    score = max(_MIN_SCORE, min(score, _MAX_SCORE))

    # Telemetry
    if log:
        log_stability_score(score, context="identity_checks.score_identity_stability")
        # If anchors helped, optionally emit anchor glyph
        if emit_glyphs and len(anchors) > 0:
            log_glyph_emission("G∅λ", context="anchors_contributed")

    # For completeness, include a lightweight event for downstream dashboards.
    log_event(
        "identity_stability_evaluated",
        score=score,
        drift_count=len(drift_events),
        anchors=[a.phrase for a in anchors],
    )

    return score


__all__ = ["check_collapse_drift", "has_collapse_drift", "score_identity_stability"]