# harness/analysis/eval_cli.py
from __future__ import annotations
import argparse, json, csv
import numpy as np
from typing import Tuple
from .endpoint_eval import evaluate_identity_vs_null

def _load_xi_Pt(csv_path: str) -> Tuple[np.ndarray, np.ndarray]:
    xi_vals = []
    Pt_vals = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # xi is blank at t=0; skip blanks safely
            xi_str = (row.get("xi") or "").strip()
            if xi_str != "":
                try:
                    xi_vals.append(float(xi_str))
                except ValueError:
                    pass
            Pt_str = (row.get("Pt") or "").strip()
            if Pt_str != "":
                try:
                    Pt_vals.append(float(Pt_str))
                except ValueError:
                    pass
    return np.asarray(xi_vals, dtype=float), np.asarray(Pt_vals, dtype=float)

def evaluate_from_csv(identity_csv: str, null_csv: str) -> dict:
    xi_id, Pt_id = _load_xi_Pt(identity_csv)
    xi_nu, Pt_nu = _load_xi_Pt(null_csv)
    return evaluate_identity_vs_null(xi_id, xi_nu, Pt_id, Pt_nu)

def main():
    ap = argparse.ArgumentParser(description="Evaluate RC+ξ endpoints from Identity and Null CSVs.")
    ap.add_argument("--identity_csv", required=True, help="Per-turn CSV for Identity run")
    ap.add_argument("--null_csv", required=True, help="Per-turn CSV for Null run")
    ap.add_argument("--out_json", required=True, help="Path to write JSON summary")
    args = ap.parse_args()

    out = evaluate_from_csv(args.identity_csv, args.null_csv)
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    # also print a compact line for quick logs
    print(json.dumps(out, separators=(",", ":")))

if __name__ == "__main__":
    main()
