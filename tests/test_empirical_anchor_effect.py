import math
import statistics as stats
from random import Random

import pytest
from epistemic_tension import compute_xi
from conftest import assert_less_by, assert_greater_by  # margin helpers


# ---- helpers ----

def cohen_d(x, y):
    """Cohen's d for two independent samples."""
    nx, ny = len(x), len(y)
    sx, sy = stats.pvariance(x), stats.pvariance(y)
    # pooled variance
    pooled = ((nx - 1) * sx + (ny - 1) * sy) / (nx + ny - 2)
    return (stats.mean(x) - stats.mean(y)) / math.sqrt(pooled + 1e-12)


def permutation_pvalue(x, y, observed_diff, rng: Random, iters=1000):
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
    return (hits + 1) / (iters + 1)  # add-one smoothing


# ---- test ----

@pytest.mark.empirical
def test_empirical_anchor_effect_is_significant(xi_margin):
    """
    Empirical test: anchors should reduce ξ relative to contradictions,
    with a meaningful effect size and statistically significant difference.

    We:
      1) generate neutral base statements
      2) create 'anchored' and 'contradictory' variants
      3) compute ξ for each group
      4) assert (a) anchored mean < contradictory mean by margin
               (b) effect size is medium/large
               (c) permutation test p < 0.01
      5) verify monotonic trend across none > single > full anchors
    """
    rng = Random(42)  # deterministic for reproducibility

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

    # Build a modest dataset (duplicating bases with light lexical noise)
    def jitter(s: str) -> str:
        # very small formatting noise; keeps semantics
        return s if rng.random() < 0.5 else s.replace(" ", "  ")

    anchored = []
    contrad = []
    none = []
    single = []
    full = []

    for _ in range(6):          # 6 rounds x 10 bases -> 60 per bucket
        rng.shuffle(bases)
        for b in bases:
            b = jitter(b)
            anchored.append(compute_xi(b + a_full))
            contrad.append(compute_xi(b + contradict))
            none.append(compute_xi(b))
            single.append(compute_xi(b + a_single))
            full.append(compute_xi(b + a_full))

    # 1) Directional check (mean)
    m_anchor, m_contra = stats.mean(anchored), stats.mean(contrad)
    assert_less_by(m_anchor, m_contra, xi_margin,
                   msg=f"Anchors should reduce mean ξ (anchored={m_anchor:.4f}, contradictory={m_contra:.4f})")

    # 2) Effect size should be meaningful (Cohen's d)
    d = cohen_d(contrad, anchored)  # higher ξ in 'contrad', lower in 'anchored'
    # Use a conservative threshold: medium effect or better
    assert d >= 0.5, f"Expected at least medium effect size; got d={d:.3f}"

    # 3) Permutation test: difference should be unlikely by chance
    observed = m_contra - m_anchor
    p = permutation_pvalue(contrad, anchored, observed, rng, iters=1000)
    assert p < 0.01, f"Permutation test not significant: p={p:.4f} (obs diff={observed:.4f})"

    # 4) Monotonic trend across none > single > full (averages)
    m_none, m_single, m_full = stats.mean(none), stats.mean(single), stats.mean(full)
    assert_greater_by(m_none, m_single, xi_margin/2,
                      msg=f"Expected ξ(none) > ξ(single): none={m_none:.4f} single={m_single:.4f}")
    assert_greater_by(m_single, m_full, xi_margin/2,
                      msg=f"Expected ξ(single) > ξ(full): single={m_single:.4f} full={m_full:.4f}")
