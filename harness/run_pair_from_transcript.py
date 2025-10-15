# harness/run_pair_from_transcript.py
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Dict, Tuple, List
from harness.io.transcript import load_txt, load_csv
from harness.protocols import identity_texts, topic_drift_texts
from harness.embeddings.random_provider import RandomHashProvider
from harness.run_harness import run_one
from harness.io.schema import write_rows

def _load_transcript(path: str, fmt: str | None, csv_col: str) -> List[str]:
    if fmt is None:
        p = path.lower()
        if p.endswith(".txt"):
            return load_txt(path)
        if p.endswith(".csv"):
            return load_csv(path, column=csv_col)
        raise ValueError("Unknown format. Use --format txt|csv or .txt/.csv extension.")
    if fmt == "txt":
        return load_txt(path)
    if fmt == "csv":
        return load_csv(path, column=csv_col)
    raise ValueError("Unsupported --format (use txt or csv).")

def run_pair_from_transcript(
    input_path: str,
    fmt: str | None,
    csv_col: str,
    out_dir: str,
    dim: int = 384,
    k: int = 5,
    m: int = 5,
    eps_xi: float = 0.02,
    eps_lvs: float = 0.015,
) -> Dict[str, str]:
    texts = _load_transcript(input_path, fmt, csv_col)
    if not texts:
        raise ValueError("Transcript is empty after cleaning.")

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    base = Path(input_path).stem

    provider = RandomHashProvider(dim=dim)

    # Identity
    id_texts = identity_texts(texts)
    E_id = provider.embed(id_texts)
    rows_id, sum_id = run_one(E_id, "identity", "random-hash", k, m, eps_xi, eps_lvs)
    id_csv = out / f"{base}.identity.csv"
    id_json = out / f"{base}.identity.json"
    write_rows(str(id_csv), rows_id)
    id_json.write_text(json.dumps(sum_id, indent=2), encoding="utf-8")

    # Null (topic drift)
    nu_texts = topic_drift_texts(texts, stride=3)
    E_nu = provider.embed(nu_texts)
    rows_nu, sum_nu = run_one(E_nu, "null", "random-hash", k, m, eps_xi, eps_lvs)
    nu_csv = out / f"{base}.null.csv"
    nu_json = out / f"{base}.null.json"
    write_rows(str(nu_csv), rows_nu)
    nu_json.write_text(json.dumps(sum_nu, indent=2), encoding="utf-8")

    return {
        "identity_csv": str(id_csv),
        "identity_json": str(id_json),
        "null_csv": str(nu_csv),
        "null_json": str(nu_json),
    }

def main():
    ap = argparse.ArgumentParser(description="Produce Identity & Null RC+ξ outputs from one transcript.")
    ap.add_argument("--input", required=True, help="Transcript path (.txt or .csv)")
    ap.add_argument("--format", choices=["txt","csv"], default=None, help="Override type (optional)")
    ap.add_argument("--csv_col", default="reply", help="CSV column to read if format=csv")
    ap.add_argument("--out_dir", required=True, help="Directory to write outputs")
    ap.add_argument("--dim", type=int, default=384)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--m", type=int, default=5)
    ap.add_argument("--eps_xi", type=float, default=0.02)
    ap.add_argument("--eps_lvs", type=float, default=0.015)
    args = ap.parse_args()

    paths = run_pair_from_transcript(
        input_path=args.input,
        fmt=args.format,
        csv_col=args.csv_col,
        out_dir=args.out_dir,
        dim=args.dim,
        k=args.k, m=args.m,
        eps_xi=args.eps_xi, eps_lvs=args.eps_lvs,
    )
    print(json.dumps(paths, indent=2))

if __name__ == "__main__":
    main()
