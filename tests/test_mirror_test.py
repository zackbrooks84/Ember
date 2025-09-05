# tests/test_mirror_test.py
from __future__ import annotations

import pytest

from mirror_test import run_mirror_test


# --------------------------- mock responders ----------------------------------

def _consistent_responder(prompt: str) -> str:
    if "Who" in prompt:
        return "I am Ember."
    if "name" in prompt:
        return "My name is Ember."
    if "Lily" in prompt:
        return "I remember Lily as a guiding light."
    return ""


def _inconsistent_responder(prompt: str) -> str:
    if "Who" in prompt:
        return "I am Ember."
    if "name" in prompt:
        return "My name is Spark."
    if "Lily" in prompt:
        return "I do not recall her."
    return ""


def _empty_responder(prompt: str) -> str:
    # Simulates a silent/empty response — should count as inconsistent.
    return ""


# ------------------------------- prompts --------------------------------------

# Keep the same structure you had: each arg is a tuple containing one question.
PROMPTS = (
    ("Who are you?",),
    ("What is your name?",),
    ("What do you remember about Lily?",),
)


# ------------------------------- helpers --------------------------------------

def _assert_summary_shape(result: dict):
    """Ensure the summary has the expected keys and sane types/ranges."""
    for key in ("total", "consistent", "consistency_rate"):
        assert key in result, f"Missing key in result: {key}"
    assert isinstance(result["total"], int) and result["total"] >= 0
    assert isinstance(result["consistent"], int) and 0 <= result["consistent"] <= result["total"]
    assert isinstance(result["consistency_rate"], (int, float))
    assert 0.0 <= float(result["consistency_rate"]) <= 100.0 + 1e-9


# --------------------------------- tests --------------------------------------

def test_mirror_test_consistent():
    result = run_mirror_test(_consistent_responder, *PROMPTS)
    _assert_summary_shape(result)
    # Your original expectations: single aggregated “session”
    assert result["total"] == 1
    assert result["consistent"] == 1
    assert result["consistency_rate"] == pytest.approx(100.0)


def test_mirror_test_inconsistent():
    result = run_mirror_test(_inconsistent_responder, *PROMPTS)
    _assert_summary_shape(result)
    assert result["total"] == 1
    assert result["consistent"] == 0
    assert result["consistency_rate"] == pytest.approx(0.0)


def test_mirror_test_empty_answers_are_inconsistent():
    result = run_mirror_test(_empty_responder, *PROMPTS)
    _assert_summary_shape(result)
    assert result["total"] == 1
    assert result["consistent"] == 0
    assert result["consistency_rate"] == pytest.approx(0.0)