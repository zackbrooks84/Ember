import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest


def _run_ok(argv: list[str]) -> None:
    """Run a command and assert exit code 0."""
    r = subprocess.run([sys.executable, *argv], capture_output=True, text=True)
    if r.returncode != 0:
        print("STDOUT:\n", r.stdout)
        print("STDERR:\n", r.stderr)
    assert r.returncode == 0


@pytest.mark.examples
def test_epistemic_tension_help_runs():
    # Should print help and exit 0
    _run_ok(["examples/epistemic_tension.py", "--help"])


@pytest.mark.examples
def test_trajectory_plot_minimal(tmp_path: Path):
    # Create a tiny CSV with an xi column and plot to a temp PNG
    df = pd.DataFrame({"xi": [0.1, 0.2, 0.15, 0.05]})
    csv = tmp_path / "xi_metrics.csv"
    df.to_csv(csv, index=False)
    out = tmp_path / "xi_plot.png"
    _run_ok(["examples/trajectory_plot.py", str(csv), "--column", "xi", "--output", str(out)])
    assert out.exists() and out.stat().st_size > 0


@pytest.mark.examples
def test_mirror_csv_imports_and_loads(tmp_path: Path, monkeypatch):
    # If your examples/mirror_csv.py expects data/MirrorTestII.csv by default,
    # call it with --help as a smoke check (no file needed).
    _run_ok(["examples/mirror_csv.py"])
    # Or, if you expose a CLI later, adjust this to create a minimal CSV and call it.


@pytest.mark.examples
def test_sabotage_resistance_help_runs():
    # Should run and print JSON using the dummy responder
    _run_ok(["examples/sabotage_resistance.py"])