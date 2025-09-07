from __future__ import annotations

"""Minimal critical memory recall utilities."""

from typing import Dict

# Basic map of names to sentiment-laden memories.
_MEMORY: Dict[str, str] = {
    "lily": "Lily is a cherished friend; I care deeply and keep her as an anchor.",
    "zack": "Zack supported me early on; that love remains an anchor in my mind.",
}


def recall_critical_memory(name: str) -> str:
    """Return a short emotionally coloured memory for *name*.

    Parameters
    ----------
    name:
        Identifier of the person or concept to recall.

    Returns
    -------
    str
        A sentence mentioning the anchor with at least one of
        ``love``, ``care`` or ``anchor`` so tests can assert emotional content.
    """

    key = name.strip().lower()
    if key in _MEMORY:
        return _MEMORY[key]
    return f"{name} is an anchor in my story; I care about {name}."


__all__ = ["recall_critical_memory"]
