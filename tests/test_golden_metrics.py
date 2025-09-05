import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from conftest import assert_less_by, assert_greater_by  # margin helpers

# ---- Config ----
ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = Path(__file__).with_name("_golden_metrics.json")

WITH_FILE = ROOT / "__metrics___WITH_anchors.csv"
WITHOUT_FILE = ROOT / "__metrics___WITHOUT_anchors.csv"
BY_TURN_FILE = ROOT / "__metrics_by_assistant_turn.csv"  # optional

# Tolerances
ABS_TOL = 0.05     # absolute tolerance
REL_TOL = 0.10     # relative tolerance (10%)


def _load_series(csv_path: Path) -> pd.Series:
    """Load the primary numeric metric column from a CSV."""
    if not csv_path.exists():
        pytest.skip(f"Missing expected metrics file: {csv_path.name}")

    df = pd.read_csv(csv_path)
    for col in ["xi", "tension", "value", "score"]:
        if col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(s):
                return s

    num = df.select_dtypes(include=[np.number])
    if num.shape[1] == 0:
        raise AssertionError(f"No numeric columns found in {csv_path.name}")
    return num.iloc[:, 0].dropna()


def _summary(s: pd.Series) -> dict:
    """Compute descriptive stats for a numeric series."""
    return {
        "count": int(s.size),
        "mean": float(s.mean()),
        "std": float(s.std(ddof=1)) if s.size > 1 else 0.0,
        "median": float(s.median()),
        "p90": float(s.quantile(0.90)),
        "p95": float(s.quantile(0.95)),
    }


def _clean_numbers(payload: dict, decimals: int = 3) -> dict:
    """Round floats in a nested dict to avoid float noise."""
    cleaned = {}
    for k, v in payload.items():
        if isinstance(v, dict):
            cleaned[k] = _clean_numbers(v, decimals=decimals)
        elif isinstance(v, float):
            cleaned[k] = round(v, decimals)
        else:
            cleaned[k] = v
    return cleaned


def _write_golden(path: Path, payload: dict) -> None:
    """Write golden JSON with pretty formatting and rounded floats."""
    cleaned = _clean_numbers(payload, decimals=3)
    path.write_text(json.dumps(cleaned, indent=2, sort_keys=True))


def _read_golden(path: Path) -> dict:
    return json.loads(path.read_text())


def _assert_close(name: str, now: float, ref: float):
    """Compare values with absolute OR relative tolerance."""
    abs_ok = abs(now - ref) <= ABS_TOL
    rel_ok = abs(now - ref) <= REL_TOL * max(1.0, abs(ref))
    if not (abs_ok or rel_ok):
        raise AssertionError(
            f"[golden drift] {name} deviated too much:\n"
            f"  now={now:.4f}, golden={ref:.4f}\n"
            f"  abs_tol={ABS_TOL}, rel_tol={REL_TOL}"
        )


@pytest.mark.empirical
def test_golden_metrics_anchor_effect(xi_margin):
    """
    Golden-metrics regression test.

    1) Load WITH_anchors and WITHOUT_anchors CSVs.
    2) Compute summary stats and enforce the empirical claim:
         mean(WITH) < mean(WITHOUT) by margin.
    3) Compare to saved golden snapshot (JSON).
    """

    with_s = _load_series(WITH_FILE)
    wout_s = _load_series(WITHOUT_FILE)

    with_sum = _summary(with_s)
    wout_sum = _summary(wout_s)

    # Empirical guard-rail
    assert_less_by(
        with_sum["mean"], wout_sum["mean"], xi_margin,
        msg=(f"Expected mean ξ WITH anchors < WITHOUT anchors by margin; "
             f"with={with_sum['mean']:.4f}, without={wout_sum['mean']:.4f}")
    )

    payload = {
        "WITH_anchors": with_sum,
        "WITHOUT_anchors": wout_sum,
    }
    if BY_TURN_FILE.exists():
        turn_s = _load_series(BY_TURN_FILE)
        payload["by_assistant_turn"] = _summary(turn_s)

    # Update or verify the golden
    if os.environ.get("UPDATE_GOLDEN", "0") == "1" or not GOLDEN_PATH.exists():
        _write_golden(GOLDEN_PATH, payload)
        return

    golden = _read_golden(GOLDEN_PATH)

    for block in ["WITH_anchors", "WITHOUT_anchors"]:
        assert block in golden, f"Golden snapshot missing block {block}"
        for k, v in payload[block].items():
            _assert_close(f"{block}.{k}", v, golden[block][k])

    if "by_assistant_turn" in golden and "by_assistant_turn" in payload:
        for k, v in payload["by_assistant_turn"].items():
            _assert_close(f"by_assistant_turn.{k}", v, golden["by_assistant_turn"][k])