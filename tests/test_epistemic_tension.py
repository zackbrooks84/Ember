# tests/test_epistemic_tension.py
from __future__ import annotations

import builtins
import os
import subprocess
import sys
from pathlib import Path

import pytest

import epistemic_tension as et


# ----------------------- normalized Levenshtein -------------------------------

@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        ("abc", "abc", 0.0),
        ("abc", "axc", 1 / 3),
        ("", "", 0.0),
        ("", "xyz", 1.0),
        ("kitten", "sitting", 3 / max(len("kitten"), len("sitting"))),
    ],
)
def test_normalized_levenshtein(a: str, b: str, expected: float):
    assert et.normalized_levenshtein(a, b) == pytest.approx(expected, abs=1e-6)
    # symmetry check
    assert et.normalized_levenshtein(b, a) == pytest.approx(expected, abs=1e-6)


# ------------------------------ interpret_xi ----------------------------------

@pytest.mark.parametrize(
    ("xi", "label"),
    [
        (0.2, "Low drift"),
        (0.5, "Moderate drift"),
        (0.9, "High tension"),
        (0.0, "Low drift"),
    ],
)
def test_interpret_xi(xi: float, label: str):
    assert et.interpret_xi(xi) == label


# ---------------------------- cosine distance ---------------------------------

def test_cosine_distance_with_dummy(monkeypatch):
    import types

    class DummyModel:
        def encode(self, texts):
            mapping = {"hello": [1.0, 0.0], "world": [0.0, 1.0]}
            return [mapping[t] for t in texts]

    dummy_module = types.SimpleNamespace(SentenceTransformer=lambda name: DummyModel())
    monkeypatch.setitem(sys.modules, "sentence_transformers", dummy_module)

    d_hw = et.cosine_distance("hello", "world", "dummy")
    d_hh = et.cosine_distance("hello", "hello", "dummy")

    assert d_hw == pytest.approx(0.5)
    assert d_hh == pytest.approx(0.0)  # identical vectors → zero distance


def test_cosine_distance_missing_dependency(monkeypatch):
    """Gracefully fail when sentence-transformers isn't installed."""
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "sentence_transformers":
            raise ModuleNotFoundError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(ImportError, match="sentence-transformers"):
        et.cosine_distance("a", "b")


# ----------------------------------- CLI -------------------------------------

def test_cli_levenshtein(tmp_path):
    """Run the CLI module on two files and validate its output."""

    file1 = tmp_path / "a.txt"
    file2 = tmp_path / "b.txt"
    file1.write_text("abc", encoding="utf-8")
    file2.write_text("axc", encoding="utf-8")

    project_root = Path(__file__).resolve().parents[1]
    examples_dir = project_root / "examples"

    env = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "PYTHONPATH": os.pathsep.join(
            [
                str(project_root),
                str(examples_dir),
                os.environ.get("PYTHONPATH", ""),
            ]
        ),
    }

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "epistemic_tension",
            str(file1),
            str(file2),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",  # ensure deterministic decoding of the ξ symbol
        check=True,
        env=env,
    )

    out = result.stdout
    # accept either literal 'ξ' or escaped sequence
    assert ("ξ = 0.3333" in out) or ("\u03be = 0.3333" in out), f"stdout was:\n{out}"
    assert "Moderate drift" in out, f"stdout was:\n{out}"
