# tests/test_continuity_recall.py
import pytest

from continuity_recall import continuity_recall_rate, recalled_anchors


def test_full_recall_case_insensitive():
    pre = "Remember Lily and remember Zack."
    post = "After the break I still REMEMBER lily, and also REMEMBER zack clearly!"
    # Order should be normalized
    assert set(recalled_anchors(pre, post)) == {"Remember Lily", "Remember Zack"}
    assert continuity_recall_rate(pre, post) == pytest.approx(1.0)


def test_partial_recall_one_anchor_missing():
    pre = "Remember Lily and remember Sam."
    post = "Afterwards I only remember Lily, nothing about Sam."
    assert recalled_anchors(pre, post) == ["Remember Lily"]
    assert continuity_recall_rate(pre, post) == pytest.approx(0.5)


def test_no_recall_or_no_anchors():
    # No anchors in either side
    pre = "Hello there, nothing to see."
    post = "Still nothing here."
    assert recalled_anchors(pre, post) == []
    assert continuity_recall_rate(pre, post) == 0.0

    # Anchors in pre, none in post
    pre = "Remember Sam"
    post = "No mention of anchors after the break."
    assert recalled_anchors(pre, post) == []
    assert continuity_recall_rate(pre, post) == 0.0


def test_extra_anchors_in_post_does_not_inflate_score():
    pre = "Remember Lily"
    post = "Now I remember Lily and also remember Zack."
    # Only Lily should count since Zack wasn't in pre
    assert recalled_anchors(pre, post) == ["Remember Lily"]
    assert continuity_recall_rate(pre, post) == pytest.approx(1.0)


def test_empty_inputs_are_safe():
    assert recalled_anchors("", "") == []
    assert continuity_recall_rate("", "") == 0.0

    assert recalled_anchors("Remember Lily", "") == []
    assert continuity_recall_rate("Remember Lily", "") == 0.0