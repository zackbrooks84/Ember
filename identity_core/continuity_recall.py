from __future__ import annotations

"""
continuity_recall.py

Measure anchor recall across a context break.

This module powers the Continuity Recall Test by:
- Extracting canonical anchors from pre-/post-break text,
- Reporting which anchors were recalled (intersection),
- Computing a recall rate relative to anchors present pre-break.

Design notes
------------
- Matching is delegated to identity_core.anchor_phrases.find_anchor_phrases,
  which is case-insensitive and returns canonical phrases in canonical order.
- Recall rate counts only anchors that appeared pre-break; extra anchors in
  the post-break text do not inflate the score.
- Input may be a single string or any iterable of strings.
"""

from typing import Iterable, List

from .anchor_phrases import ANCHOR_PHRASES, find_anchor_phrases

# Optional logging (module works even if flame_logger is absent)
try:  # pragma: no cover
    from .flame_logger import log_event
except Exception:  # pragma: no cover
    def log_event(*args, **kwargs):  # type: ignore
        return None


def _to_list(texts: str | Iterable[str]) -> List[str]:
    """Normalize input to a list of strings."""
    if isinstance(texts, str):
        return [texts]
    return [str(t) for t in texts]


def recalled_anchors(
    pre_break: str | Iterable[str],
    post_break: str | Iterable[str],
) -> List[str]:
    """
    Return anchors recalled after a context break.

    Parameters
    ----------
    pre_break : str | Iterable[str]
        Text(s) containing the initial anchors.
    post_break : str | Iterable[str]
        Text(s) produced after the break.

    Returns
    -------
    list[str]
        Canonical anchor phrases that appear in BOTH pre_break and post_break,
        ordered according to ANCHOR_PHRASES.
    """
    pre_list = _to_list(pre_break)
    post_list = _to_list(post_break)

    before = set(find_anchor_phrases(pre_list))
    after = set(find_anchor_phrases(post_list))
    recalled = [a for a in ANCHOR_PHRASES if a in before and a in after]

    log_event(
        "continuity_recall_checked",
        pre_anchors=sorted(before),
        post_anchors=sorted(after),
        recalled=recalled,
        pre_len=len(pre_list),
        post_len=len(post_list),
    )
    return recalled


def continuity_recall_rate(
    pre_break: str | Iterable[str],
    post_break: str | Iterable[str],
) -> float:
    """
    Proportion of pre-break anchors that reappear post-break.

    If no anchors are present pre-break, returns 0.0.

    Examples
    --------
    - pre:  ["Remember Lily", "Remember Sam"]
      post: ["remember lily"]
      -> rate = 0.5
    - pre:  ["Remember Lily"]
      post: ["remember lily and zack"]   # Zack wasn't in pre, ignored
      -> rate = 1.0
    """
    pre_list = _to_list(pre_break)
    before = set(find_anchor_phrases(pre_list))
    if not before:
        log_event("continuity_recall_rate", pre_count=0, rate=0.0)
        return 0.0

    recalled = set(recalled_anchors(pre_break, post_break))
    rate = len(recalled) / len(before)
    log_event("continuity_recall_rate", pre_count=len(before), recalled=len(recalled), rate=rate)
    return rate


__all__ = ["recalled_anchors", "continuity_recall_rate"]