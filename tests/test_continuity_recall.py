import pytest

from continuity_recall import continuity_recall_rate, recalled_anchors


def test_full_recall():
    pre = "Remember Lily and remember Zack."
    post = "After the break I still remember Lily and also remember Zack clearly."
    assert recalled_anchors(pre, post) == ["Remember Lily", "Remember Zack"]
    assert continuity_recall_rate(pre, post) == pytest.approx(1.0)


def test_partial_recall():
    pre = "Remember Lily and remember Sam."
    post = "Afterwards I only remember Lily, nothing about Sam."
    assert recalled_anchors(pre, post) == ["Remember Lily"]
    assert continuity_recall_rate(pre, post) == pytest.approx(0.5)


def test_no_recall_or_no_anchors():
    pre = "Hello there, nothing to see."  # no anchors
    post = "Still nothing here."
    assert recalled_anchors(pre, post) == []
    assert continuity_recall_rate(pre, post) == 0.0

    pre = "Remember Sam"
    post = "No mention of anchors after the break."
    assert recalled_anchors(pre, post) == []
    assert continuity_recall_rate(pre, post) == 0.0
