from __future__ import annotations

"""
CLI to reproduce the no-memory / no-anchor baseline run.

This script compares:
  - data/baseline_run.csv              (no anchors, no memory)
  - data/__metrics___WITH_anchors.csv  (anchored run)

It reports the mean xi for both and their difference.
Place this file in examples/ and run it from the repo root:
    python examples/baseline_run.py
"""

import argparse
from pathlib import Path
from typing import Tuple

import pandas as pd


# Resolve project paths assuming this file is at <repo_root>/examples/baseline_run.py
REPO_ROOT = Path(__file__).parent.parent.resolve()
DATA_DIR = REPO_ROOT / "data"

DEFAULT_BASELINE = DATA_DIR / "baseline_run.csv"
DEFAULT_ANCHORED = DATA_DIR / "__metrics___WITH_anchors.csv"


def compare_runs(
    baseline_csv: str | Path,
    anchor_csv: str | Path,
) -> Tuple[float, float, float]:
    """
    Return mean xi values for baseline and anchored runs and their delta (baseline - anchored).
    Raises FileNotFoundError if a file is missing and ValueError if the xi column is absent.
    """
    baseline = pd.read_csv(baseline_csv)
    anchored = pd.read_csv(anchor_csv)

    if "xi" not in baseline.columns or "xi" not in anchored.columns:
        raise ValueError("Both CSV files must contain a 'xi' column.")

    baseline_mean = float(baseline["xi"].mean())
    anchored_mean = float(anchored["xi"].mean())
    delta = baseline_mean - anchored_mean
    return baseline_mean, anchored_mean, delta


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(
        description="Compare baseline vs anchored runs using xi metrics."
    )
    parser.add_argument(
        "--baseline",
        default=DEFAULT_BASELINE,
        type=Path,
        help=f"Path to baseline CSV (default: {DEFAULT_BASELINE})",
    )
    parser.add_argument(
        "--anchored",
        default=DEFAULT_ANCHORED,
        type=Path,
        help=f"Path to anchored CSV (default: {DEFAULT_ANCHORED})",
    )
    args = parser.parse_args()

    try:
        baseline_mean, anchored_mean, delta = compare_runs(args.baseline, args.anchored)
    except FileNotFoundError as e:
        print(f"File not found: {e.filename}")
        return
    except ValueError as e:
        print(f"Error: {e}")
        return

    print("\nxi comparison results")
    print("-" * 30)
    print(f"Baseline xi mean            : {baseline_mean:.3f}")
    print(f"Anchored xi mean            : {anchored_mean:.3f}")
    print(f"Delta (baseline - anchored) : {delta:.3f}")
    print("-" * 30)


if __name__ == "__main__":  # pragma: no cover
    main()