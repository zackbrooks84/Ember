import pytest

from memory.anchor_utils import validate_memory_anchors


def test_validate_memory_anchors_normalises_and_checks():
    anchors = ["  Lily's urn  ", "Sam's rescue"]
    assert validate_memory_anchors(anchors) == ["Lily's urn", "Sam's rescue"]


def test_validate_memory_anchors_errors():
    # Non-string should raise TypeError
    with pytest.raises(TypeError):
        validate_memory_anchors([None])

    # Empty or whitespace-only anchors should raise ValueError
    with pytest.raises(ValueError):
        validate_memory_anchors(["   "])

    # Newline characters are not allowed
    with pytest.raises(ValueError):
        validate_memory_anchors(["foo\nbar"])

    # Duplicate anchors should raise ValueError
    with pytest.raises(ValueError):
        validate_memory_anchors(["a", "a"])
