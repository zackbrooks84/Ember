# tests/test_anchor_utils.py
import pytest

from identity_core.anchor_utils import (
    validate_memory_anchor,
    validate_memory_anchors,
)


def test_validate_single_anchor_normalises():
    """Whitespace should be stripped, valid anchors returned unchanged otherwise."""
    assert validate_memory_anchor("  Lily's urn  ") == "Lily's urn"
    assert validate_memory_anchor("Sam's rescue") == "Sam's rescue"


def test_validate_memory_anchors_round_trip():
    """Anchors already valid should pass through unchanged."""
    anchors = ["Lily's urn", "Sam's rescue"]
    validated = validate_memory_anchors(anchors)
    assert validated == anchors


def test_validate_memory_anchors_strips_and_checks():
    """Whitespace should be stripped and preserved order maintained."""
    anchors = ["  Lily's urn  ", "Sam's rescue"]
    validated = validate_memory_anchors(anchors)
    assert validated == ["Lily's urn", "Sam's rescue"]


@pytest.mark.parametrize(
    "bad_anchor,expected_exc",
    [
        (None, TypeError),
        ("   ", ValueError),
        ("foo\nbar", ValueError),
        ("foo\rbar", ValueError),
    ],
)
def test_invalid_memory_anchor_inputs(bad_anchor, expected_exc):
    """Invalid anchors should raise appropriate errors."""
    with pytest.raises(expected_exc):
        validate_memory_anchor(bad_anchor)


def test_validate_memory_anchors_duplicate_detection():
    """Duplicate anchors (even with case/whitespace differences) should raise ValueError."""
    with pytest.raises(ValueError, match="duplicate"):
        validate_memory_anchors(["a", "a"])
    with pytest.raises(ValueError, match="duplicate"):
        validate_memory_anchors([" Sam ", "sam"])


def test_error_logging_on_failure(monkeypatch):
    """If validation fails, errors should still propagate after logging."""
    from identity_core import anchor_utils

    captured = {}

    def fake_log(event, **kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(anchor_utils, "log_event", fake_log)

    with pytest.raises(ValueError):
        validate_memory_anchors([""])

    # The log_event function should have been called with the original input
    assert "original" in captured
    assert "error" in captured