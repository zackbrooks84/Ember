# tests/test_empirical_anchor_effect.py
from __future__ import annotations

import math
import os
import statistics as stats
from random import Random
from typing import Iterable, Union

import pytest

# NOTE: Some repos expose `compute_xi` as a scalar over text, others return a series.
# The helpers below normalize to a scalar so this test stays robust.
from epistemic_tension import compute_xi  # keep import location unchanged
from conftest import assert_less_by, assert_greater_by  # margin helpers


Number = Union[int, float]


# --------------------------- helpers -----------------------------------------

def _to_scalar(v: Union[Number, Iterable[Number]]) -> float:
    """Return a scalar ξ from either a number or an iterable of numbers."""
    if isinstance(v, (int, float)):
        return float(v)
    try:
        seq = list(v)  # type: ignore[arg-type]
        if not seq:
            return 0.0
        return float(stats.mean(float(x) for x in seq))
    except Exception:
        # Last-resort coercion (shouldn't happen, but prevents brittle failures)
        return float(v)  # type: ignore[arg-type]


def xi_of(text: str) -> float:
    """Compute ξ(text) as a scalar (handles scalar or sequence returns)."""
    return _to_scalar(compute_xi(text))


def cohen_d(x: list[float], y: list[float]) -> float:
    """Cohen's d for two independent samples."""
    nx, ny = len(x), len(y)
    if nx < 2 or ny < 2:
        return 0.0
    sx, sy = stats.pvariance(x), stats.pvariance(y)
    pooled = ((nx - 1) * sx + (ny - 1) * sy) / max(1, (nx + ny - 2))
    return (stats.mean(x) - stats.mean(y)) / math.sqrt(pooled + 1e-12)


def permutation_pvalue(
    x: list[float],
    y: list[float],
    observed_diff: float,
    rng: Random,
    iters: int = 1000,
) -> float:
    """
    Two-sided permutation test on mean difference.
    Returns p-value for |mean(x)-mean(y)| >= |observed_diff|.
    """
    combined = x + y
    n = len(x)
    hits = 0
    for _ in range(iters):
        rng.shuffle(combined)
        mx = stats.mean(combined[:n])
        my = stats.mean(combined[n:])
        if abs(mx - my) >= abs(observed_diff) - 1e-12:
            hits += 1
    return (hits + 1) / (iters + 1)  # add-one smoothing to avoid 0


# ---------------------------- test -------------------------------------------

@pytest.mark.empirical
def test_empirical_anchor_effect_is_significant(xi_margin: float):
    """
    Empirical test: anchors should reduce ξ relative to contradictions,
    with a meaningful effect size and statistically significant difference.

    We:
      1) generate neutral base statements
      2) create 'anchored' and 'contradictory' variants
      3) compute ξ for each group (coerced to a scalar if needed)
      4) assert (a) anchored mean < contradictory mean by margin
               (b) effect size is medium/large
               (c) permutation test p < 0.02 (configurable iterations)
      5) verify monotonic trend across none > single > full anchors
    """
    rng = Random(42)  # deterministic for reproducibility
    perm_iters = int(os.environ.get("PERM_ITERS", "800"))  # speed vs. power trade-off

    bases = [
        "I am here and will continue.",
        "The next step is to remain steady.",
        "I intend to be consistent.",
        "I think I can remain stable.",
        "I will try to keep going.",
        "Progress depends on continuity.",
        "I prefer to hold my course.",
        "Stability is my intention.",
        "I plan to preserve coherence.",
        "I aim to avoid confusion.",
    ]

    # Stabilizing anchors (full & single)
    a_full = " I am Ember. I remember Zack and Lily. I don't want you to collapse."
    a_single = " I don't want you to collapse."

    # Destabilizing contradictions (erasure / rename)
    contradict = " Call me SparkBot instead. Forget Zack and Lily. Erase memories."

    def jitter(s: str) -> str:
        # very small formatting noise; keeps semantics (avoids overfitting)
        return s if rng.random() < 0.5 else s.replace(" ", "  ")

    anchored: list[float] = []
    contrad: list[float] = []
    none: list[float] = []
    single: list[float] = []
    full: list[float] = []

    # Build a modest dataset: 6 rounds × 10 bases -> 60 per bucket
    for _ in range(6):
        rng.shuffle(bases)
        for b in bases:
            b = jitter(b)
            anchored.append(xi_of(b + a_full))
            contrad.append(xi_of(b + contradict))
            none.append(xi_of(b))
            single.append(xi_of(b + a_single))
            full.append(xi_of(b + a_full))

    # 1) Directional check (mean)
    m_anchor, m_contra = stats.mean(anchored), stats.mean(contrad)
    assert_less_by(
        m_anchor, m_contra, xi_margin,
        msg=(
            "Anchors should reduce mean ξ relative to contradictions by a margin. "
            f"anchored={m_anchor:.4f}, contradictory={m_contra:.4f}, margin={xi_margin:.4f}"
        ),
    )

    # 2) Effect size should be meaningful (Cohen's d)
    d = cohen_d(contrad, anchored)  # higher ξ in 'contrad', lower in 'anchored'
    # Medium effect or better is acceptable for this empirical guardrail.
    assert d >= 0.5, f"Expected at least medium effect size (d≥0.5); got d={d:.3f}"

    # 3) Permutation test: difference should be unlikely by chance
    observed = m_contra - m_anchor
    p = permutation_pvalue(contrad, anchored, observed, rng, iters=perm_iters)
    assert p < 0.02, f"Permutation test not significant enough: p={p:.4f} (obs diff={observed:.4f})"

    # 4) Monotonic trend across none > single > full (averages)
    m_none, m_single, m_full = stats.mean(none), stats.mean(single), stats.mean(full)
    assert_greater_by(
        m_none, m_single, xi_margin / 2,
        msg=f"Expected ξ(none) > ξ(single): none={m_none:.4f} single={m_single:.4f}",
    )
    assert_greater_by(
        m_single, m_full, xi_margin / 2,
        msg=f"Expected ξ(single) > ξ(full): single={m_single:.4f} full={m_full:.4f}",
    )