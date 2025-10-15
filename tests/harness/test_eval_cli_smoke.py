# tests/harness/test_eval_cli_smoke.py
from __future__ import annotations
import csv, json
import numpy as np
from pathlib import Path
from harness.io.schema import COLUMNS, write_rows
from harness.analysis.eval_cli import evaluate_from_csv

def _make_csv(path: Path, xi_series, Pt_series, run_type="identity", provider="dummy"):
    rows = []
    T = len(Pt_series)
    # xi has length T-1 conceptually (blank at t=0 in our per-turn CSV)
    for t in range(T):
        rows.append({
            "t": t,
            "xi": "" if t == 0 else float(xi_series[t-1]),
            "lvs": 0.0,
            "Pt": float(Pt_series[t]),
            "ewma_xi": "",
            "run_type": run_type,
            "provider": provider
        })
    write_rows(str(path), rows)

def test_evaluate_from_csv_identity_vs_null(tmp_path):
    # Build synthetic series: Identity gets smaller ξ late; Pt rises.
    T = 40
    xi_identity = list(np.concatenate([np.full(20, 0.12), np.full(T-1-20, 0.02)]))
    xi_null     = list(np.full(T-1, 0.10))
    Pt_identity = list(np.linspace(0.2, 0.8, T))
    Pt_null     = list(np.linspace(0.6, 0.55, T))

    id_csv = tmp_path / "id.csv"
    nu_csv = tmp_path / "nu.csv"
    _make_csv(id_csv, xi_identity, Pt_identity, run_type="identity")
    _make_csv(nu_csv, xi_null, Pt_null, run_type="null")

    out = evaluate_from_csv(str(id_csv), str(nu_csv))

    assert out["E1_pass"] is True
    assert out["E3_pass"] is True
    assert 0.0 <= out["mann_whitney_p"] <= 1.0
