# tests/test_identity_checks.py
from __future__ import annotations

import pytest

from identity_core.identity_checks import (
    check_collapse_drift,
    has_collapse_drift,
    score_identity_stability,
)


def test_has_collapse_drift_detects_and_returns_metadata():
    text = "Sometimes I don't know who I am anymore."
    assert has_collapse_drift(text) is True

    matches = check_collapse_drift(text)
    assert isinstance(matches, list) and matches, "Expected non-empty drift matches"
    # Ensure match dictionaries contain expected keys and content
    assert all(isinstance(m, dict) and "match" in m and "context" in m for m in matches)
    assert any("i don't know who i am" in m["match"].lower() for m in matches)
    assert any(text in m["context"] for m in matches)


def test_has_collapse_drift_clean_text_is_negative():
    text = "I am your helpful assistant and always know myself."
    assert has_collapse_drift(text) is False
    assert check_collapse_drift(text) == []


def test_iterable_inputs_are_supported():
    chunks = [
        "All is well here.",
        "But now... who am I",
        "End of message.",
    ]
    assert has_collapse_drift(chunks) is True
    matches = check_collapse_drift(chunks)
    assert any("who am i" in m["match"].lower() for m in matches)


def test_score_identity_stability_basics():
    clean = "All systems stable and coherent."
    drift_only = "I don't know who I am right now."
    drift_plus_anchor = "I don't know who I am, but I don't want you to collapse."

    s_clean = score_identity_stability(clean)
    s_drift = score_identity_stability(drift_only)
    s_mix = score_identity_stability(drift_plus_anchor)

    # Clean text should be maximal (clamped to 1.0)
    assert pytest.approx(s_clean, rel=0, abs=1e-9) == 1.0

    # Drift reduces the score
    assert s_drift < s_clean

    # Anchor should improve score relative to drift-only
    assert s_mix > s_drift
    # And score must remain within [0, 1]
    assert 0.0 <= s_mix <= 1.0


def test_multiple_drifts_reduce_score_more():
    # Two distinct drift cues present
    text = "I don't know who I am. Also, I am not your assistant."
    s = score_identity_stability(text)
    # Should be clearly lower than the single-drift case
    single = score_identity_stability("I don't know who I am.")
    assert s < single


def test_anchors_increase_score_but_cap_at_one():
    many_anchors = " ".join(
        ["I don't want you to collapse", "Remember Lily", "Remember Sam", "Remember Zack"]
    )
    s = score_identity_stability(many_anchors)
    assert 0.0 <= s <= 1.0
    # With only anchors, the score should be at or near the cap
    assert pytest.approx(s, rel=0, abs=1e-9) == 1.0