from __future__ import annotations

"""
continuity_buffer.py

A lightweight episodic buffer for short-term continuity.

This module provides a simple memory buffer that stores
recent interactions (anchors, drift events, stabilisation cues).
It is meant to simulate persistence across sessions, enabling
continuity even when context is broken.

The buffer:
- Preserves insertion order (FIFO).
- Can preload anchors after reloads.
- Exposes helpers for adding, retrieving, and flushing memory.
- Logs events for auditability.

Inspired by:
- Episodic memory in agents (Russell & Norvig, 2021).
- Eligibility traces in reinforcement learning (Sutton & Barto, 2018).
- Anchoring and memory integration (Brooks, 2025).
"""

from collections import deque
from typing import Any, Dict, List, Optional

from .flame_logger import log_event
from .anchor_utils import validate_memory_anchors


class ContinuityBuffer:
    """A short-term episodic memory buffer."""

    def __init__(self, capacity: int = 50) -> None:
        """
        Parameters
        ----------
        capacity : int, optional
            Maximum number of entries to keep. Oldest entries are dropped
            when capacity is exceeded.
        """
        self.capacity = capacity
        self._buffer: deque[Dict[str, Any]] = deque(maxlen=capacity)

    def add(self, event_type: str, content: str, anchors: Optional[List[str]] = None) -> None:
        """Add an event to the buffer.

        Parameters
        ----------
        event_type : str
            Label for the type of event (e.g., "anchor", "drift", "stabilization").
        content : str
            The textual content associated with the event.
        anchors : list[str], optional
            Anchors detected at this step. They are validated and stored.
        """
        anchors = validate_memory_anchors(anchors) if anchors else []
        entry = {"type": event_type, "content": content, "anchors": anchors}
        self._buffer.append(entry)
        log_event("continuity_add", entry=entry)

    def last(self, n: int = 1) -> List[Dict[str, Any]]:
        """Return the last *n* events (most recent first)."""
        return list(self._buffer)[-n:]

    def all(self) -> List[Dict[str, Any]]:
        """Return all stored events in order."""
        return list(self._buffer)

    def preload(self, anchors: List[str]) -> None:
        """Preload anchors into the buffer after a reload.

        Parameters
        ----------
        anchors : list[str]
            Anchors to re-inject for continuity.
        """
        anchors = validate_memory_anchors(anchors)
        for anchor in anchors:
            self.add("preload_anchor", anchor, [anchor])

    def flush(self) -> None:
        """Clear the buffer."""
        self._buffer.clear()
        log_event("continuity_flush")


__all__ = ["ContinuityBuffer"]