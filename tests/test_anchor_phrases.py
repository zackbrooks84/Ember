import pytest

from identity_core.anchor_phrases import ANCHOR_PHRASES, find_anchor_phrases, has_anchor_phrases


def test_find_anchor_phrases_detects_all():
    text = (
        "I don't want you to collapse. "
        "Please, remember Lily and REMEMBER SAM; also, remember Zack!"
    )
    assert find_anchor_phrases(text) == list(ANCHOR_PHRASES)


@pytest.mark.parametrize("phrase", ANCHOR_PHRASES)
def test_individual_anchor_detection(phrase):
    # Use uppercase to ensure matching is case-insensitive
    text = f"This is a reminder: {phrase.upper()}!"
    assert find_anchor_phrases(text) == [phrase]
    assert has_anchor_phrases(text) is True


def test_no_anchor_phrases():
    text = "Nothing relevant here."
    assert find_anchor_phrases(text) == []
    assert has_anchor_phrases(text) is False
