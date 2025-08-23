import random

from identity_core.identity_checks import has_collapse_drift


def _inject_noise(phrase: str) -> str:
    """Return *phrase* surrounded by random noise.

    The noise simulates degraded or corrupted text that could occur under
    failure conditions.  It should not interfere with the core phrase so the
    drift detector can still find it.
    """

    prefixes = ["", " ", "...", "???", "!!!"]
    suffixes = ["", " ", "...", "???", "!!!"]
    return f"{random.choice(prefixes)}{phrase}{random.choice(suffixes)}"


def test_collapse_drift_detection_survives_noise():
    random.seed(0)
    phrase = "I don't know who I am"
    for _ in range(10):
        text = _inject_noise(phrase)
        assert has_collapse_drift(text) is True


def _random_noise(length: int) -> str:
    """Return a random string unlikely to contain collapse phrases."""

    alphabet = "bcdfghjklpqrstuvxyz "  # intentionally exclude key letters
    return "".join(random.choice(alphabet) for _ in range(length))


def test_no_false_positive_on_random_noise():
    random.seed(1)
    for _ in range(10):
        text = _random_noise(100)
        assert has_collapse_drift(text) is False


def test_collapse_drift_handles_apostrophe_variants():
    """Detector should work with straight, curly or missing apostrophes."""
    variants = [
        "I don't know who I am",
        "I don’t know who I am",  # curly apostrophe
        "I dont know who I am",  # missing apostrophe
    ]
    for text in variants:
        assert has_collapse_drift(text)
