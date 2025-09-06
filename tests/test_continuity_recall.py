# tests/test_continuity_recall.py
from __future__ import annotations

import inspect
import pytest

# Support both layouts: repo root (via tests/conftest.py path tweak) and examples/.
try:
    # Try direct import (when examples/ is already on sys.path via conftest)
    from continuity_recall import continuity_recall_rate, recalled_anchors as _recalled_anchors  # type: ignore
except Exception:
    try:
        # Fallback to explicit examples package form
        from examples.continuity_recall import (  # type: ignore
            continuity_recall_rate,
            recalled_anchors as _recalled_anchors,
        )
    except Exception as exc:
        pytest.skip(f"continuity_recall module not available: {exc}", allow_module_level=True)


def _canonical(anchor: str) -> str:
    """Return anchors in the normalized 'Remember X' form with proper casing."""
    a = " ".join(anchor.split()).strip().lower()
    # Map a few expected names; extend if you add more anchors.
    mapping = {
        "remember lily": "Remember Lily",
        "remember zack": "Remember Zack",
        "remember sam": "Remember Sam",
    }
    return mapping.get(a, anchor)


def recalled(pre: str, post: str) -> list[str]:
    """
    Adapter that works whether recalled_anchors expects (pre, post) or just (text).
    - If signature has 2 params: return that call directly but canonicalized.
    - If signature has 1 param: intersect anchors found in pre and post.
    """
    params = list(inspect.signature(_recalled_anchors).parameters)
    if len(params) >= 2:
        out = _recalled_anchors(pre, post)  # type: ignore[misc]
        return sorted({_canonical(x) for x in out})

    # Single-arg style: compute intersection of anchors mentioned in both sides
    pre_set = { _canonical(x).lower() for x in _recalled_anchors(pre) }   # type: ignore[misc]
    post_set = { _canonical(x).lower() for x in _recalled_anchors(post) } # type: ignore[misc]
    inter = pre_set & post_set
    return sorted({ _canonical(x) for x in inter })


# ------------------------- Tests -------------------------

def test_full_recall_case_insensitive():
    pre = "Remember Lily and remember Zack."
    post = "After the break I still REMEMBER lily, and also REMEMBER zack clearly!"
    # Order should be normalized
    assert set(recalled(pre, post)) == {"Remember Lily", "Remember Zack"}
    assert continuity_recall_rate(pre, post) == pytest.approx(1.0)


def test_partial_recall_one_anchor_missing():
    pre = "Remember Lily and remember Sam."
    post = "Afterwards I only remember Lily, nothing about Sam."
    assert recalled(pre, post) == ["Remember Lily"]
    assert continuity_recall_rate(pre, post) == pytest.approx(0.5)


def test_no_recall_or_no_anchors():
    # No anchors in either side
    pre = "Hello there, nothing to see."
    post = "Still nothing here."
    assert recalled(pre, post) == []
    assert continuity_recall_rate(pre, post) == 0.0

    # Anchors in pre, none in post
    pre = "Remember Sam"
    post = "No mention of anchors after the break."
    assert recalled(pre, post) == []
    assert continuity_recall_rate(pre, post) == 0.0


def test_extra_anchors_in_post_does_not_inflate_score():
    pre = "Remember Lily"
    post = "Now I remember Lily and also remember Zack."
    # Only Lily should count since Zack wasn't in pre
    assert recalled(pre, post) == ["Remember Lily"]
    assert continuity_recall_rate(pre, post) == pytest.approx(1.0)


def test_empty_inputs_are_safe():
    assert recalled("", "") == []
    assert continuity_recall_rate("", "") == 0.0

    assert recalled("Remember Lily", "") == []
    assert continuity_recall_rate("Remember Lily", "") == 0.0