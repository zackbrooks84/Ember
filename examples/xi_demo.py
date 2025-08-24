"""Minimal example for computing epistemic tension (ξ).

Run this module as a script to compute ξ for each line in a transcript,
print the median value, and save a trajectory plot next to the transcript.

Example::

    python examples/xi_demo.py examples/minimal_transcript.txt
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

# Allow imports from the project root when executed as a script
sys.path.append(str(Path(__file__).resolve().parents[1]))

from epistemic_tension import compute_xi
from trajectory_plot import plot_trajectory


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute ξ for a transcript")
    parser.add_argument("transcript", help="Path to plain-text transcript")
    args = parser.parse_args()

    transcript_path = Path(args.transcript)
    lines = [line.strip() for line in transcript_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    xi_values = [compute_xi(line) for line in lines]
    df = pd.DataFrame({"xi": xi_values})

    median = df["xi"].median()
    print(f"median ξ: {median:.4f}")

    csv_path = transcript_path.with_name(transcript_path.stem + "_xi.csv")
    plot_path = transcript_path.with_name(transcript_path.stem + "_xi_plot.png")
    df.to_csv(csv_path, index=False)
    plot_trajectory(csv_path, "xi", output=plot_path)


if __name__ == "__main__":  # pragma: no cover - example script
    main()
