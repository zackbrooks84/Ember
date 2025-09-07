from __future__ import annotations

"""Plot epistemic tension (ξ) or coherence trajectories over time.

This lightweight utility helps visualise how the tension metric ``ξ`` or a
coherence measure ``Ψ`` evolves throughout a conversation.  It reads a CSV file
containing the metric values and produces a line plot, optionally including a
windowed trajectory :math:`W(t)` (rolling mean) to smooth short term
fluctuations.  The resulting graph mirrors the plots referenced in Appendix A of
the project write-up.

Usage
-----
Running the module as a script expects the path to a CSV file.  The column to
plot defaults to ``xi`` but can be changed with ``--column``.  When ``--window``
is provided the rolling mean is plotted alongside the raw series.

Example::

    python examples/trajectory_plot.py xi_metrics.csv --column xi --window 5 --output xi.png

"""

from pathlib import Path
import argparse

import pandas as pd
import matplotlib.pyplot as plt


def windowed_trajectory(series: pd.Series, window: int) -> pd.Series:
    """Return a rolling mean of ``series`` using the specified ``window`` size.

    The computation includes the current point and ``window - 1`` preceding
    points.  The first ``window - 1`` values are calculated with progressively
    larger partial windows so the result retains the original length.
    """

    if window <= 0:
        raise ValueError("window must be positive")
    return series.rolling(window, min_periods=1).mean()


def plot_trajectory(
    csv_path: str | Path,
    column: str = "xi",
    window: int | None = None,
    output: str | Path | None = None,
) -> None:
    """Plot the trajectory stored in ``column`` of ``csv_path``.

    Parameters
    ----------
    csv_path:
        File containing the metrics.  Must be readable by :func:`pandas.read_csv`.
    column:
        Name of the column to plot (``"xi"`` by default).
    window:
        If provided, the size of the rolling window used to compute
        :math:`W(t)` and overlay it on the plot.
    output:
        Optional path to save the generated figure.  When omitted the plot is
        displayed interactively.
    """

    df = pd.read_csv(csv_path)
    if column not in df.columns:
        raise ValueError(f"column '{column}' not found in {csv_path}")

    x = df["timestamp"] if "timestamp" in df.columns else range(len(df))
    y = df[column]

    plt.figure()
    plt.plot(x, y, label=column)
    if window:
        plt.plot(x, windowed_trajectory(y, window), label=f"W{window}")
    plt.xlabel("time" if "timestamp" in df.columns else "index")
    plt.ylabel(column)
    plt.legend()
    plt.tight_layout()

    if output:
        plt.savefig(output)
    else:  # pragma: no cover - manual usage
        plt.show()


def main() -> None:  # pragma: no cover - CLI entry point
    parser = argparse.ArgumentParser(
        description="Plot ξ or Ψ(t) trajectories from a metrics CSV file.",
    )
    parser.add_argument("csv", help="Path to CSV file containing metrics")
    parser.add_argument(
        "--column",
        default="xi",
        help="Name of the column to plot (default: xi)",
    )
    parser.add_argument(
        "--window",
        type=int,
        help="Optional window size for computing W(t)",
    )
    parser.add_argument(
        "--output",
        help="File to save the plot; if omitted the plot window is shown",
    )
    args = parser.parse_args()
    plot_trajectory(args.csv, args.column, args.window, args.output)


__all__ = ["plot_trajectory", "windowed_trajectory"]


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
