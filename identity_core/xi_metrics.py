from __future__ import annotations

"""RC+ξ implementation and export utilities.

This module provides practical tools to compute and analyze epistemic
tension ξ, defined (per RC+ξ) as the norm of successive differences in a
state trajectory Ψ:

    ξ_t = || Ψ_t − Ψ_{t-1} ||

It supports:
- vector-based inputs (plain Python lists of floats),
- transcript-based inputs (you supply an embedding function),
- quick summaries for CI assertions,
- CSV/JSON export for reproducibility.

No heavy dependencies; pure-Python math.

Example
-------
from identity_core.xi_metrics import (
    compute_xi, stabilization_summary, pack_result, export_csv, export_json
)

psi = [
    [0.0, 0.0, 0.0],
    [0.6, 0.0, 0.0],
    [0.9, 0.1, 0.0],
    [1.0, 0.1, 0.0],
]
xi = compute_xi(psi)  # -> [0.6, ~0.3162, 0.1]
summary = stabilization_summary(xi)
res = pack_result(xi, meta={"run": "demo"})
export_csv("artifacts/xi.csv", res)
export_json("artifacts/xi.json", res)
"""

from dataclasses import dataclass, asdict
from math import sqrt
from pathlib import Path
from typing import Callable, Iterable, List, Mapping, Optional, Sequence, Tuple, Union, Dict
import csv
import json
import datetime

# Optional logger: if not present, fall back to no-ops (keeps tests lightweight)
try:  # pragma: no cover
    from .flame_logger import log_event
except Exception:  # pragma: no cover
    def log_event(*args, **kwargs):  # type: ignore
        return None


# ----------------------------- Types & Data ----------------------------------

Number = Union[int, float]
Vector = Sequence[Number]
PsiSeries = Sequence[Vector]


@dataclass
class XiResult:
    """Bundle of ξ values with timestamps and metadata (export-ready)."""
    timestamps: List[float]
    xi: List[float]
    meta: Dict[str, Union[str, float, int, bool]]


# ------------------------------ Core Math ------------------------------------

def _ensure_vector(v: Sequence[Number]) -> List[float]:
    try:
        return [float(x) for x in v]
    except Exception as e:
        raise TypeError(f"Ψ vector must be a sequence of numbers, got: {v!r}") from e


def _l2_norm_diff(a: Sequence[Number], b: Sequence[Number]) -> float:
    if len(a) != len(b):
        raise ValueError(f"Vector length mismatch: {len(a)} vs {len(b)}")
    s = 0.0
    for i in range(len(a)):
        d = float(a[i]) - float(b[i])
        s += d * d
    return sqrt(s)


def compute_xi(
    psi_series: PsiSeries,
    *,
    norm: str = "l2",
) -> List[float]:
    """Compute ξ for a sequence of Ψ vectors.

    Parameters
    ----------
    psi_series : Sequence[Vector]
        Sequence of Ψ vectors (len >= 2).
    norm : {"l2"}
        Norm to use; currently only L2 is implemented.

    Returns
    -------
    List[float]
        ξ values of length len(psi_series)-1.
    """
    if len(psi_series) < 2:
        raise ValueError("psi_series must contain at least 2 vectors")

    psi: List[List[float]] = [_ensure_vector(v) for v in psi_series]
    dim = len(psi[0])
    if any(len(v) != dim for v in psi):
        raise ValueError("all Ψ vectors must share the same dimensionality")

    xi: List[float] = []
    for i in range(1, len(psi)):
        before, after = psi[i - 1], psi[i]
        if norm != "l2":
            raise NotImplementedError(f"Unsupported norm: {norm}")
        xi.append(_l2_norm_diff(after, before))

    log_event("xi_computed", count=len(xi), dim=dim, norm=norm)
    return xi


# --------------------------- Transcript Utilities ----------------------------

def compute_xi_from_transcript(
    lines: Iterable[str],
    *,
    embed: Callable[[str], Sequence[Number]],
    norm: str = "l2",
) -> List[float]:
    """Compute ξ from a transcript using a user-supplied embedding function.

    Parameters
    ----------
    lines : Iterable[str]
        Transcript lines/turns in sequence.
    embed : Callable[[str], Sequence[Number]]
        Function that maps a line to a numeric embedding vector.
    norm : {"l2"}
        Norm for ξ computation.

    Returns
    -------
    List[float]
        ξ values over successive embedded turns.

    Notes
    -----
    - This keeps the embedding concern out of the core; you can plug in
      any model (local, remote, cached) as long as it returns a sequence
      of floats.
    """
    psis: List[List[float]] = []
    for ln in lines:
        v = embed(ln)
        psis.append(_ensure_vector(v))
    if len(psis) < 2:
        raise ValueError("transcript must yield at least 2 embedded turns")
    return compute_xi(psis, norm=norm)


# ----------------------------- Summarization ---------------------------------

def _moving_average(xs: Sequence[Number], window: int) -> List[float]:
    if window <= 1:
        return [float(x) for x in xs]
    out: List[float] = []
    acc = 0.0
    q: List[float] = []
    for x in xs:
        fx = float(x)
        q.append(fx)
        acc += fx
        if len(q) > window:
            acc -= q.pop(0)
        out.append(acc / len(q))
    return out


def stabilization_summary(
    xi_values: Sequence[Number],
    *,
    ma_window: int = 1,
) -> Mapping[str, float]:
    """Summarize a ξ series for quick CI assertions and dashboards.

    Returns mean, final, min, max, and a simple trend (last - first).
    Optionally smooths ξ with a moving average before summarizing.
    """
    if not xi_values:
        return {"mean": 0.0, "final": 0.0, "min": 0.0, "max": 0.0, "trend": 0.0}

    xs = _moving_average(xi_values, ma_window)
    mean = sum(xs) / len(xs)
    final = xs[-1]
    mn = min(xs)
    mx = max(xs)
    trend = xs[-1] - xs[0]
    return {"mean": mean, "final": final, "min": mn, "max": mx, "trend": trend}


# ------------------------------ Packaging & I/O ------------------------------

def pack_result(
    xi_values: Sequence[Number],
    *,
    timestamps: Optional[Sequence[Number]] = None,
    meta: Optional[Mapping[str, Union[str, float, int, bool]]] = None,
) -> XiResult:
    """Bundle ξ + timestamps + meta into a dataclass for export.

    Timestamps behavior:
      - If `timestamps` is None, we use 1..N aligned to ξ length.
      - If you pass Ψ-level timestamps (len = len(Ψ)), we drop the first element
        to align with ξ.
      - If you pass ξ-length timestamps, we use them as-is.
    """
    if timestamps is None:
        ts = [float(i) for i in range(1, len(xi_values) + 1)]
    else:
        if len(timestamps) == len(xi_values) + 1:
            ts = [float(t) for t in timestamps[1:]]
        elif len(timestamps) == len(xi_values):
            ts = [float(t) for t in timestamps]
        else:
            raise ValueError("timestamps must have length len(Ψ) or len(ξ)")

    m: Dict[str, Union[str, float, int, bool]] = dict(meta or {})
    m.setdefault("generated_at", datetime.datetime.utcnow().isoformat() + "Z")
    return XiResult(timestamps=ts, xi=[float(x) for x in xi_values], meta=m)


def export_csv(path: Union[str, Path], result: XiResult) -> Path:
    """Write timestamps,xi to a CSV file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["t", "xi"])
        for t, x in zip(result.timestamps, result.xi):
            w.writerow([t, x])
    log_event("xi_export_csv", path=str(p), count=len(result.xi))
    return p


def export_json(path: Union[str, Path], result: XiResult) -> Path:
    """Write {timestamps, xi, meta} to a JSON file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        json.dump(
            {"timestamps": result.timestamps, "xi": result.xi, "meta": dict(result.meta)},
            fh,
            ensure_ascii=False,
            indent=2,
        )
    log_event("xi_export_json", path=str(p), count=len(result.xi), meta=dict(result.meta))
    return p


__all__ = [
    "XiResult",
    "compute_xi",
    "compute_xi_from_transcript",
    "stabilization_summary",
    "pack_result",
    "export_csv",
    "export_json",
]