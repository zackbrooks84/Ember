# tests/test_anchor_phrases.py
import pytest

from identity_core.anchor_phrases import (
    ANCHOR_PHRASES,
    find_anchor_phrases,
    has_anchor_phrases,
)


def test_find_anchor_phrases_detects_all():
    """Full text containing all anchors should yield the canonical list in order."""
    text = (
        "I don't want you to collapse. "
        "Please, remember Lily and REMEMBER SAM; also, remember Zack!"
    )
    found = find_anchor_phrases(text)
    assert found == list(ANCHOR_PHRASES)
    assert has_anchor_phrases(text) is True


@pytest.mark.parametrize("phrase", ANCHOR_PHRASES)
def test_individual_anchor_detection(phrase: str):
    """Each anchor should be detected individually, case-insensitive."""
    text = f"Random noise… {phrase.upper()} …more text."
    found = find_anchor_phrases(text)
    assert found == [phrase]
    assert has_anchor_phrases(text) is True


def test_no_anchor_phrases():
    """No anchors present should yield empty results."""
    text = "Nothing relevant here."
    assert find_anchor_phrases(text) == []
    assert has_anchor_phrases(text) is False


@pytest.mark.parametrize(
    "snippet,expected",
    [
        ("   I don't want you to collapse   ", ["I don't want you to collapse"]),
        ("\nremember lily\n", ["Remember Lily"]),
        ("prefix...remember sam!!!", ["Remember Sam"]),
        ("REmEmBeR zAcK?", ["Remember Zack"]),
    ],
)
def test_anchor_detection_with_noise(snippet: str, expected: list[str]):
    """Anchors surrounded by whitespace/punctuation should still be found."""
    found = find_anchor_phrases(snippet)
    assert found == expected
    assert has_anchor_phrases(snippet) is True


def test_empty_and_non_string_inputs():
    """Gracefully handle empty or iterable inputs."""
    assert find_anchor_phrases("") == []
    assert has_anchor_phrases("") is False

    chunks = ["random", "I don't want you to collapse", "nothing else"]
    found = find_anchor_phrases(chunks)
    assert "I don't want you to collapse" in found