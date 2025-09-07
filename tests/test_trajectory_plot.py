# tests/test_trajectory_plot.py
from __future__ import annotations

from pathlib import Path

import pandas as pd
import matplotlib
import pytest

# Use a non-interactive backend for CI
matplotlib.use("Agg")

from examples.trajectory_plot import windowed_trajectory, plot_trajectory


# --------------------------- windowed_trajectory ------------------------------

@pytest.mark.parametrize(
    "values,window,expected",
    [
        # Your original case (simple rolling mean with window=2)
        ([1, 2, 3, 4], 2, [1.0, 1.5, 2.5, 3.5]),
        # Identity when window=1
        ([0.1, 0.2, 0.3], 1, [0.1, 0.2, 0.3]),
        # Window > length — should still produce same-length output with min_periods handling
        ([5, 7], 10, [5.0, 6.0]),
    ],
)
def test_windowed_trajectory(values, window, expected):
    s = pd.Series(values, dtype="float64")
    out = windowed_trajectory(s, window=window)
    # Ensure same length and numeric dtype
    assert len(out) == len(s)
    assert out.dtype.kind in ("f", "i")
    # Numerical equality with reasonable tolerance
    assert pytest.approx(expected) == out.tolist()

def test_windowed_trajectory_monotonic_on_increasing_input():
    s = pd.Series([1, 2, 3, 4, 5], dtype="float64")
    out = windowed_trajectory(s, window=3)
    # Moving average over increasing values should be non-decreasing
    assert all(x2 >= x1 for x1, x2 in zip(out.tolist(), out.tolist()[1:]))


# -------------------------------- plot_trajectory -----------------------------

def _write_csv(path: Path) -> None:
    df = pd.DataFrame(
        {
            "timestamp": [1, 2, 3, 4, 5],
            "xi": [0.32, 0.28, 0.25, 0.22, 0.20],
        }
    )
    df.to_csv(path, index=False)

def _is_png(path: Path) -> bool:
    try:
        with path.open("rb") as fh:
            sig = fh.read(8)
        # PNG signature: 89 50 4E 47 0D 0A 1A 0A
        return sig == b"\x89PNG\r\n\x1a\n"
    except Exception:
        return False


def test_plot_trajectory(tmp_path: Path):
    csv = tmp_path / "data.csv"
    _write_csv(csv)

    output = tmp_path / "plot.png"
    ret = plot_trajectory(csv, window=2, output=output)

    # Function may return None or the output Path — accept both
    assert ret is None or Path(ret) == output

    # File exists, non-empty, and has a PNG signature
    assert output.exists() and output.stat().st_size > 0
    assert _is_png(output), "Output file is not a valid PNG"



def test_plot_trajectory_with_nondefault_window(tmp_path: Path):
    csv = tmp_path / "data2.csv"
    _write_csv(csv)

    output = tmp_path / "plot_w3.png"
    plot_trajectory(csv, window=3, output=output)

    assert output.exists() and output.stat().st_size > 0
    assert _is_png(output), "Output file is not a valid PNG"
