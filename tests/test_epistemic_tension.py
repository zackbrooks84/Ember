import subprocess
import sys
from pathlib import Path

import pytest

import epistemic_tension as et


def test_normalized_levenshtein():
    assert et.normalized_levenshtein("abc", "abc") == 0.0
    assert et.normalized_levenshtein("abc", "axc") == pytest.approx(1 / 3)


def test_interpret_xi():
    assert et.interpret_xi(0.2) == "Low drift"
    assert et.interpret_xi(0.5) == "Moderate drift"
    assert et.interpret_xi(0.9) == "High tension"


def test_cosine_distance_with_dummy(monkeypatch):
    import types

    class DummyModel:
        def encode(self, texts):
            mapping = {"hello": [1.0, 0.0], "world": [0.0, 1.0]}
            return [mapping[t] for t in texts]

    dummy_module = types.SimpleNamespace(SentenceTransformer=lambda name: DummyModel())
    monkeypatch.setitem(sys.modules, "sentence_transformers", dummy_module)

    distance = et.cosine_distance("hello", "world", "dummy")
    assert distance == pytest.approx(0.5)


def test_cli_levenshtein(tmp_path):
    file1 = tmp_path / "a.txt"
    file2 = tmp_path / "b.txt"
    file1.write_text("abc", encoding="utf-8")
    file2.write_text("axc", encoding="utf-8")

    script = Path(__file__).resolve().parents[1] / "epistemic_tension.py"
    result = subprocess.run(
        [sys.executable, str(script), str(file1), str(file2)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "\u03be = 0.3333" in result.stdout
    assert "Moderate drift" in result.stdout
