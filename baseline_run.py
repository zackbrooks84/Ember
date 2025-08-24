from __future__ import annotations

"""CLI to reproduce the no-memory/no-anchor baseline run.

This utility compares the bundled baseline metrics with the anchored
run to highlight the drift contrast described in the paper.  By default
it reads ``tests/data/baseline_run.csv`` (no anchors or memory) and
``tests/data/__metrics___WITH_anchors.csv`` (anchored) and reports the
mean ``ξ`` values and their difference.
"""

import argparse
from pathlib import Path

import pandas as pd

BASELINE_CSV = (
    Path(__file__).resolve().parent / "tests" / "data" / "baseline_run.csv"
)
ANCHOR_CSV = Path(__file__).resolve().parent / "tests" / "data" / "__metrics___WITH_anchors.csv"


def compare_runs(baseline_csv: str | Path, anchor_csv: str | Path) -> tuple[float, float, float]:
    """Return mean ξ values for baseline and anchored runs and their delta."""
    baseline = pd.read_csv(baseline_csv)
    anchored = pd.read_csv(anchor_csv)
    baseline_mean = baseline["xi"].mean()
    anchored_mean = anchored["xi"].mean()
    return baseline_mean, anchored_mean, baseline_mean - anchored_mean


def main() -> None:  # pragma: no cover - CLI entry point
    parser = argparse.ArgumentParser(
        description="Compare baseline vs anchored runs using ξ metrics.",
    )
    parser.add_argument(
        "--baseline",
        default=str(BASELINE_CSV),
        help="Path to no-memory/no-anchor baseline CSV",
    )
    parser.add_argument(
        "--anchored",
        default=str(ANCHOR_CSV),
        help="Path to anchored run CSV",
    )
    args = parser.parse_args()

    baseline_mean, anchored_mean, delta = compare_runs(args.baseline, args.anchored)
    print(f"Baseline ξ mean: {baseline_mean:.2f}")
    print(f"Anchored ξ mean: {anchored_mean:.2f}")
    print(f"Δξ (baseline - anchored): {delta:.2f}")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
