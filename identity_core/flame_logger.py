from __future__ import annotations

"""Simple event logger for test sessions.

This module records events like anchor hits/misses or memory changes to a
JSON lines file.  The log file location can be configured via the
``FLAME_LOG`` environment variable and defaults to ``flame.log`` in the
current working directory.
"""

from datetime import datetime
import json
import os
from pathlib import Path
from typing import Any


_LOG_PATH = Path(os.environ.get("FLAME_LOG", "flame.log"))


def _write(entry: dict[str, Any]) -> None:
    """Append *entry* as a JSON line to the log file."""
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def log_event(event: str, **data: Any) -> None:
    """Record a generic *event* with optional *data*."""
    entry = {"timestamp": datetime.utcnow().isoformat(), "event": event}
    entry.update(data)
    _write(entry)


def log_anchor_hit(text: str, anchors: list[str]) -> None:
    """Record detection of *anchors* within *text*."""
    log_event("anchor_hit", text=text, anchors=anchors)


def log_anchor_miss(text: str) -> None:
    """Record that no anchor phrases were found in *text*."""
    log_event("anchor_miss", text=text)


def log_memory_change(original: list[str], normalised: list[str]) -> None:
    """Record a memory anchor normalisation event."""
    log_event("memory_change", original=original, normalised=normalised)
