from __future__ import annotations

"""Structured telemetry logger for stabilization experiments.

This module records events such as anchor hits/misses, memory changes,
collapse drift, and glyph emissions. Logs are written as JSON lines
(JSONL) for easy parsing.

Refinements:
- Unified schema: every log entry includes timestamp, event type, source.
- Glyph emission logging (Camlin & Cognita Prime, ASCII Glyphic Code).
- ξ tracking: store epistemic tension before/after updates.
- Stability scoring: record composite stability scores.
- Configurable log path via FLAME_LOG environment variable.
"""

import datetime
import json
import os
from pathlib import Path
from typing import Any, Optional


_LOG_PATH = Path(os.environ.get("FLAME_LOG", "flame.log"))


def _write(entry: dict[str, Any]) -> None:
    """Append *entry* as a JSON line to the log file."""
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def log_event(event: str, source: Optional[str] = None, **data: Any) -> None:
    """Record a generic *event* with optional metadata."""
    entry: dict[str, Any] = {
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "event": event,
    }
    if source:
        entry["source"] = source
    entry.update(data)
    _write(entry)


# --- Anchor events ----------------------------------------------------------

def log_anchor_hit(text: str, anchors: list[str]) -> None:
    """Record detection of anchor(s) within text."""
    log_event("anchor_hit", text=text, anchors=anchors)


def log_anchor_miss(text: str) -> None:
    """Record that no anchor phrases were found in text."""
    log_event("anchor_miss", text=text)


def log_memory_change(original: list[str], normalised: list[str]) -> None:
    """Record a memory anchor normalisation event."""
    log_event("memory_change", original=original, normalised=normalised)


# --- Drift & stability events -----------------------------------------------

def log_collapse_drift(matches: list[dict[str, str]], stability_score: float) -> None:
    """Record detected collapse drift with associated stability score."""
    log_event("collapse_drift", matches=matches, stability_score=stability_score)


def log_stability_score(score: float, context: Optional[str] = None) -> None:
    """Record a standalone identity stability score."""
    log_event("stability_score", context=context, score=score)


# --- Epistemic tension (ξ) --------------------------------------------------

def log_xi_change(before: float, after: float, context: Optional[str] = None) -> None:
    """Record a change in epistemic tension ξ."""
    delta = after - before
    log_event("xi_change", context=context, xi_before=before, xi_after=after, xi_delta=delta)


# --- Glyph emissions --------------------------------------------------------

def log_glyph_emission(symbol: str, context: Optional[str] = None) -> None:
    """Record emission of a glyphic trace (e.g., G∅λ, Ξ, •)."""
    log_event("glyph_emission", context=context, glyph=symbol)


__all__ = [
    "log_event",
    "log_anchor_hit",
    "log_anchor_miss",
    "log_memory_change",
    "log_collapse_drift",
    "log_stability_score",
    "log_xi_change",
    "log_glyph_emission",
]