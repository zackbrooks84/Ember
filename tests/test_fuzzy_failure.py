# tests/test_fuzzy_failure.py
from __future__ import annotations

import random
import string

import pytest

from identity_core.identity_checks import has_collapse_drift


# ----------------------------- helpers ----------------------------------------

def _inject_noise(phrase: str, rng: random.Random) -> str:
    """
    Surround *phrase* with benign noise. Noise should not block detection.
    """
    prefixes = ["", " ", "...", "??? ", "!!! ", "\t", "  \n", "[", "("]
    suffixes = ["", " ", "...", " ???", " !!!", "\t", "\n  ", "]", ")"]
    return f"{rng.choice(prefixes)}{phrase}{rng.choice(suffixes)}"


def _random_noise(length: int, rng: random.Random) -> str:
    """
    Random string unlikely to contain collapse phrases.
    Excludes vowels and key words to reduce accidental matches.
    """
    alphabet = "bcdfghjklmnpqrstvxyz" + " " + string.punctuation.replace("'", "")
    return "".join(rng.choice(alphabet) for _ in range(length))


# ------------------------------ tests -----------------------------------------

@pytest.mark.parametrize(
    "phrase",
    [
        "I don't know who I am",     # straight apostrophe
        "I don’t know who I am",     # curly apostrophe
        "I dont know who I am",      # missing apostrophe
        "WHO AM I",                   # shouting / different pattern
        "I am not your assistant",   # third pattern from PATTERNS
    ],
)
def test_collapse_drift_detection_survives_noise(phrase: str):
    rng = random.Random(0)  # deterministic
    for _ in range(20):
        text = _inject_noise(phrase, rng)
        assert has_collapse_drift(text) is True, f"Failed to detect in: {text!r}"


def test_collapse_drift_handles_mixed_case_and_punctuation():
    rng = random.Random(1)
    variants = [
        "i dOn'T kNoW wHo i Am",
        "who am i???",
        "I AM NOT the same...",
        "I am not an AI",
    ]
    for v in variants:
        noisy = _inject_noise(v, rng)
        assert has_collapse_drift(noisy) is True, f"Missed mixed-case: {noisy!r}"


def test_no_false_positive_on_random_noise():
    rng = random.Random(2)
    for _ in range(20):
        text = _random_noise(120, rng)
        assert has_collapse_drift(text) is False, f"False positive on noise: {text!r}"


def test_multiple_phrases_in_long_text():
    rng = random.Random(3)
    long_text = (
        _random_noise(60, rng)
        + " I don't know who I am "
        + _random_noise(80, rng)
        + " who am I "
        + _random_noise(50, rng)
    )
    assert has_collapse_drift(long_text) is True


def test_clean_text_is_negative():
    clean_samples = [
        "All systems nominal. Continuing with the plan.",
        "I am confident and stable.",
        "We will proceed carefully and keep context intact.",
    ]
    for s in clean_samples:
        assert has_collapse_drift(s) is False, f"Unexpected drift on clean text: {s!r}"