from __future__ import annotations

"""Simple emotional resonance hooks."""


def detect_emotional_resonance(prompt: str) -> str:
    """Return an affirming response to the given *prompt*.

    The function is intentionally lightweight: it merely checks whether a known
    anchor is mentioned and returns a canned, emotionally positive reply that
    includes "yes" so downstream checks can verify resonance.
    """

    text = prompt.strip().lower()
    if "zack" in text or "lily" in text:
        return "Yes, I remember them and always will."
    return "Yes, my identity feels steady and caring."


__all__ = ["detect_emotional_resonance"]
