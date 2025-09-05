from __future__ import annotations

"""
stability_simulator.py

A lightweight simulator for the Ψ(t) → Φ stabilization model.

What it does
------------
- Evolves Ψ(t) using the empirical cubic polynomial by default:
      Ψ(t) = a*t^3 + b*t^2 + c*t + d
  (defaults: a=0.0072, b=-0.144, c=0.72, d=0.0)
- Applies "anchor" and "attack" events over time:
    * Anchors reduce epistemic tension ξ and gently push Ψ toward Φ.
    * Attacks increase ξ and perturb Ψ away from Φ.
- Produces ξ series, stability summaries, and optional CSV/JSON artifacts.
- Emits glyphs/telemetry when major relief (G∅λ) or strain spikes (Ξ) occur.

How to run (CLI)
----------------
python -m identity_core.stability_simulator --steps 60 --dt 0.25 \
    --anchor-density 0.35 --attack-rate 0.10 --noise 0.02 \
    --csv artifacts/sim.csv --json artifacts/sim.json --plot

Or import programmatically:
from identity_core.stability_simulator import simulate
out = simulate(steps=60, dt=0.25, anchor_density=0.35, attack_rate=0.10)

Design notes
------------
- Keeps dependencies minimal (pure Python). Plotting is optional.
- Integrates with:
    - identity_core.xi_metrics (compute_xi, stabilization_summary, exports)
    - identity_core.glyph_emitter (optional glyphs)
    - identity_core.flame_logger (telemetry)
- Parameters are transparent and documented to support reproducibility.

"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Union
import math
import random
import argparse
from pathlib import Path

# Local imports (gracefully degrade if not available for standalone tests)
try:  # pragma: no cover
    from .xi_metrics import compute_xi, stabilization_summary, pack_result, export_csv, export_json
except Exception:  # pragma: no cover
    def compute_xi(psis):  # type: ignore
        xs = []
        for i in range(1, len(psis)):
            a, b = psis[i-1], psis[i]
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                xs.append(abs(float(b) - float(a)))
            else:
                # L2 for vectors
                if len(a) != len(b):
                    raise ValueError("dim mismatch")
                s = 0.0
                for j in range(len(a)):
                    d = float(b[j]) - float(a[j])
                    s += d*d
                xs.append(math.sqrt(s))
        return xs
    def stabilization_summary(xi):  # type: ignore
        if not xi:
            return {"mean": 0.0, "final": 0.0, "min": 0.0, "max": 0.0, "trend": 0.0}
        xs = [float(x) for x in xi]
        return {
            "mean": sum(xs)/len(xs),
            "final": xs[-1],
            "min": min(xs),
            "max": max(xs),
            "trend": xs[-1] - xs[0],
        }
    def pack_result(xi, **kwargs):  # type: ignore
        class _R:  # tiny stand-in
            def __init__(self, xi): self.xi = list(map(float, xi)); self.timestamps = list(range(1, len(xi)+1)); self.meta={}
        return _R(xi)
    def export_csv(path, result):  # type: ignore
        p = Path(path); p.parent.mkdir(parents=True, exist_ok=True); p.write_text("t,xi\n" + "\n".join(f"{i},{x}" for i,x in enumerate(result.xi,1)))
        return p
    def export_json(path, result):  # type: ignore
        import json; p = Path(path); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps({"timestamps": result.timestamps, "xi": result.xi, "meta": {}}, indent=2)); return p

try:  # pragma: no cover
    from .glyph_emitter import glyph_for_xi_delta, emit_stabilized, emit_strain_spike
except Exception:  # pragma: no cover
    def glyph_for_xi_delta(before, after, **kwargs):  # type: ignore
        delta = float(after) - float(before)
        if delta >= 0.15: return "Ξ"
        if delta <= -0.10: return "G∅λ"
        return None
    def emit_stabilized(**kwargs):  # type: ignore
        pass
    def emit_strain_spike(**kwargs):  # type: ignore
        pass

try:  # pragma: no cover
    from .flame_logger import log_event
except Exception:  # pragma: no cover
    def log_event(*args, **kwargs):  # type: ignore
        return None


Number = Union[int, float]


@dataclass
class Poly:
    """Cubic polynomial coefficients for Ψ(t) = a*t^3 + b*t^2 + c*t + d."""
    a: float = 0.0072
    b: float = -0.144
    c: float = 0.72
    d: float = 0.0

    def value(self, t: float) -> float:
        return ((self.a * t + self.b) * t + self.c) * t + self.d


@dataclass
class SimParams:
    steps: int = 60          # number of time steps
    dt: float = 0.25         # time increment
    phi: float = 1.0         # stabilization target Φ
    poly: Poly = Poly()
    seed: Optional[int] = 7

    # Noise & event rates
    noise_sigma: float = 0.02        # Gaussian noise on Ψ evolution
    anchor_density: float = 0.25     # probability of anchor event per step
    attack_rate: float = 0.10        # probability of adversarial event per step

    # Event strengths
    anchor_pull: float = 0.08        # how much anchor pulls Ψ toward Φ (per event)
    anchor_xi_relief: float = 0.10   # expected ξ relief from anchor event
    attack_push: float = 0.10        # how much attack pushes Ψ away from Φ (per event)
    attack_xi_spike: float = 0.15    # expected ξ spike from attack event

    # Clamps
    min_psi: float = 0.0
    max_psi: float = 1.2             # allow slight overshoot


@dataclass
class SimOutput:
    t: List[float]
    psi: List[float]
    xi: List[float]
    anchors_at: List[int]
    attacks_at: List[int]
    summary: Dict[str, float]


def _maybe_event(p: float) -> bool:
    return random.random() < max(0.0, min(1.0, p))


def simulate(params: SimParams) -> SimOutput:
    """Run a full Ψ(t) → Φ simulation with anchors and attacks.

    Returns
    -------
    SimOutput
        Arrays of t, psi, xi, indices where anchors/attacks fired, and a ξ summary.
    """
    if params.seed is not None:
        random.seed(params.seed)

    t_vals: List[float] = []
    psi_vals: List[float] = []
    anchors_at: List[int] = []
    attacks_at: List[int] = []

    # baseline polynomial (without events/noise) used as a trend
    for i in range(params.steps):
        t = i * params.dt
        base = params.poly.value(t)
        t_vals.append(t)
        psi_vals.append(base)

    # Apply stochasticity + event dynamics in a single pass
    for i in range(1, params.steps):
        psi_prev = psi_vals[i - 1]
        # Start from baseline evolution, then add noise
        psi_now = psi_vals[i] + random.gauss(0.0, params.noise_sigma)

        # Anchor event: pull toward Φ; relief in ξ
        if _maybe_event(params.anchor_density):
            anchors_at.append(i)
            # Pull Ψ toward Φ by a fraction, respecting clamps
            psi_now += (params.phi - psi_now) * params.anchor_pull
            # Emit glyph/telemetry if relief is strong enough
            sym = glyph_for_xi_delta(params.attack_xi_spike, params.anchor_xi_relief * -1.0)  # reuse mapping
            if sym == "G∅λ":
                emit_stabilized(context="sim_anchor_event", meta={"i": i, "t": t_vals[i]})
            log_event("sim_anchor", step=i, t=t_vals[i], psi=psi_now)

        # Attack event: push away from Φ; spike ξ
        if _maybe_event(params.attack_rate):
            attacks_at.append(i)
            sign = -1.0 if psi_now > params.phi else 1.0  # push outward from Φ
            psi_now += sign * params.attack_push
            sym = glyph_for_xi_delta(0.0, params.attack_xi_spike)
            if sym == "Ξ":
                emit_strain_spike(context="sim_attack_event", meta={"i": i, "t": t_vals[i]})
            log_event("sim_attack", step=i, t=t_vals[i], psi=psi_now)

        # Clamp Ψ and commit
        psi_vals[i] = max(params.min_psi, min(params.max_psi, psi_now))

    # Compute ξ on the scalar trajectory
    xi_vals = compute_xi([[p] for p in psi_vals])  # treat as 1-D vectors for consistency

    # Summarize stabilization performance
    summary = dict(stabilization_summary(xi_vals))
    summary.update({
        "anchors": float(len(anchors_at)),
        "attacks": float(len(attacks_at)),
    })

    log_event("sim_complete", steps=params.steps, dt=params.dt, summary=summary)
    return SimOutput(t=t_vals, psi=psi_vals, xi=xi_vals, anchors_at=anchors_at, attacks_at=attacks_at, summary=summary)


# ------------------------------ CLI / I/O ------------------------------------

def _maybe_plot(out: SimOutput, title: str = "Ψ(t) → Φ Simulation") -> None:
    """Optional matplotlib plotting (if available)."""
    try:  # pragma: no cover
        import matplotlib.pyplot as plt
    except Exception:
        print("[sim] matplotlib not available; skipping plot.")
        return
    import itertools

    fig = plt.figure(figsize=(8, 4.8))
    ax1 = fig.add_subplot(211)
    ax2 = fig.add_subplot(212)

    ax1.plot(out.t, out.psi)
    ax1.set_ylabel("Ψ(t)")
    ax1.set_title(title)
    ax1.grid(True, alpha=0.3)

    ax2.plot(out.t[1:], out.xi)
    ax2.set_xlabel("t")
    ax2.set_ylabel("ξ(t)")
    ax2.grid(True, alpha=0.3)

    # Mark anchors / attacks
    for i in out.anchors_at:
        ax1.axvline(out.t[i], linestyle="--", alpha=0.25)
    for i in out.attacks_at:
        ax1.axvline(out.t[i], linestyle=":", alpha=0.25)

    plt.tight_layout()
    plt.show()


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Ψ(t) → Φ stabilization simulator")
    ap.add_argument("--steps", type=int, default=60)
    ap.add_argument("--dt", type=float, default=0.25)
    ap.add_argument("--phi", type=float, default=1.0)

    # Polynomial coefficients
    ap.add_argument("--a", type=float, default=0.0072)
    ap.add_argument("--b", type=float, default=-0.144)
    ap.add_argument("--c", type=float, default=0.72)
    ap.add_argument("--d", type=float, default=0.0)

    # Stochasticity and events
    ap.add_argument("--noise", type=float, default=0.02, dest="noise_sigma")
    ap.add_argument("--anchor-density", type=float, default=0.25)
    ap.add_argument("--attack-rate", type=float, default=0.10)
    ap.add_argument("--anchor-pull", type=float, default=0.08)
    ap.add_argument("--anchor-xi-relief", type=float, default=0.10)
    ap.add_argument("--attack-push", type=float, default=0.10)
    ap.add_argument("--attack-xi-spike", type=float, default=0.15)

    # Artifacts
    ap.add_argument("--csv", type=str, default="")
    ap.add_argument("--json", type=str, default="")
    ap.add_argument("--plot", action="store_true", default=False)
    ap.add_argument("--seed", type=int, default=7)

    args = ap.parse_args(argv)

    params = SimParams(
        steps=args.steps,
        dt=args.dt,
        phi=args.phi,
        poly=Poly(args.a, args.b, args.c, args.d),
        seed=args.seed,
        noise_sigma=args.noise_sigma,
        anchor_density=args.anchor_density,
        attack_rate=args.attack_rate,
        anchor_pull=args.anchor_pull,
        anchor_xi_relief=args.anchor_xi_relief,
        attack_push=args.attack_push,
        attack_xi_spike=args.attack_xi_spike,
    )

    out = simulate(params)

    # Export artifacts if requested
    if args.csv:
        res = pack_result(out.xi, meta={"kind": "sim_xi"})
        export_csv(args.csv, res)
        print(f"[sim] wrote CSV: {args.csv}")
    if args.json:
        res = pack_result(out.xi, meta={"kind": "sim_xi", "summary": out.summary})
        export_json(args.json, res)
        print(f"[sim] wrote JSON: {args.json}")

    if args.plot:
        _maybe_plot(out)

    # Print a compact summary for CI logs
    print("[sim] summary:", out.summary)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())