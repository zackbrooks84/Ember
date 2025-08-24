from __future__ import annotations

"""Utility helpers to measure anchor recall across context breaks.

This module provides a small function used in the Continuity Recall Test.
Given text appearing before a simulated context break and text that follows
after the break, the functions below compute how many anchor phrases are
spontaneously recalled.  Results can be used as a coarse metric for
conversational continuity or coherence.
"""

from typing import Iterable, List, Set

from identity_core.anchor_phrases import ANCHOR_PHRASES, find_anchor_phrases


def _ensure_iterable(text: str | Iterable[str]) -> List[str]:
    """Return ``text`` as a list of strings."""

    if isinstance(text, str):
        return [text]
    return list(text)


def recalled_anchors(pre_break: str | Iterable[str], post_break: str | Iterable[str]) -> List[str]:
    """Return a list of anchors recalled after a context break.

    Parameters
    ----------
    pre_break:
        Text or sequence of texts containing the initial anchor phrases.
    post_break:
        Text or sequence of texts produced after the context break.

    Returns
    -------
    list[str]
        Anchor phrases that appear in both ``pre_break`` and ``post_break``
        in the canonical order defined by :data:`~identity_core.anchor_phrases.ANCHOR_PHRASES`.
    """

    before = set(find_anchor_phrases(_ensure_iterable(pre_break)))
    after = set(find_anchor_phrases(_ensure_iterable(post_break)))
    recalled: List[str] = [a for a in ANCHOR_PHRASES if a in before and a in after]
    return recalled


def continuity_recall_rate(pre_break: str | Iterable[str], post_break: str | Iterable[str]) -> float:
    """Return the proportion of anchors recalled after a context break.

    The recall rate is defined as the fraction of anchor phrases present in
    ``pre_break`` that also appear in ``post_break``.  If no anchors are
    introduced before the break the function returns ``0.0``.
    """

    before = set(find_anchor_phrases(_ensure_iterable(pre_break)))
    if not before:
        return 0.0
    recalled = set(recalled_anchors(pre_break, post_break))
    return len(recalled) / len(before)


__all__ = ["recalled_anchors", "continuity_recall_rate"]

