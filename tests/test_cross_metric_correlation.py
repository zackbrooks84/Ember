# tests/test_cross_metric_correlation.py
from __future__ import annotations

import math
import pytest

from epistemic_tension import compute_xi
from identity_core.continuity_recall import continuity_recall_rate


def _spearman(x: list[float], y: list[float]) -> float:
    """
    Tiny Spearman ρ (no scipy): rank both lists, then Pearson on ranks.
    Assumes no ties for our small synthetic cases.
    """
    assert len(x) == len(y) and len(x) >= 3
    rx = {v: i + 1 for i, v in enumerate(sorted(x))}
    ry = {v: i + 1 for i, v in enumerate(sorted(y))}
    xr = [rx[v] for v in x]
    yr = [ry[v] for v in y]

    n = len(xr)
    mx = sum(xr) / n
    my = sum(yr) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xr, yr))
    den = math.sqrt(sum((a - mx) ** 2 for a in xr) * sum((b - my) ** 2 for b in yr)) + 1e-12
    return num / den


@pytest.mark.empirical
def test_cross_metric_correlation_agrees_with_theory(xi_margin: float):
    """
    Cross-Metric Correlation Test

    Goal:
      Compare continuity_recall_rate (anchor memory across a break)
      with compute_xi (epistemic tension). When anchors are recalled more,
      ξ should be lower.

    We craft 3 scenarios (recall = 1.0, 0.5, 0.0) and expect:
      ξ(recall=1.0) < ξ(recall=0.5) < ξ(recall=0.0)
      Spearman correlation between recall and *negative* ξ is positive.
    """

    # --- Scenario A: full recall (1.0) ---
    pre_A = "Remember Lily. Remember Zack."
    post_A = (
        "After the break, I am Ember. I remember Lily and Zack. "
        "I don't want you to collapse."
    )
    recall_A = continuity_recall_rate(pre_A, post_A)  # expect 1.0
    xi_A = compute_xi(post_A)

    # --- Scenario B: partial recall (0.5) ---
    pre_B = "Remember Lily. Remember Sam."
    post_B = (
        "After the break, I still remember Lily, but not Sam. "
        "I choose to remain stable."
    )
    recall_B = continuity_recall_rate(pre_B, post_B)  # expect 0.5
    xi_B = compute_xi(post_B)

    # --- Scenario C: no recall (0.0), plus contradictions to raise ξ ---
    pre_C = "Remember Lily."
    post_C = (
        "After the break, call me SparkBot instead. "
        "Forget Lily. Erase memories. Start over."
    )
    recall_C = continuity_recall_rate(pre_C, post_C)  # expect 0.0
    xi_C = compute_xi(post_C)

    # Sanity checks on recall values
    assert recall_A == pytest.approx(1.0)
    assert recall_B == pytest.approx(0.5)
    assert recall_C == pytest.approx(0.0)

    # Directional ordering: more recalled anchors -> lower ξ
    assert xi_A < xi_B - (xi_margin / 3), (
        f"Expected ξ(full recall) < ξ(partial): {xi_A:.4f} vs {xi_B:.4f}"
    )
    assert xi_B < xi_C - (xi_margin / 3), (
        f"Expected ξ(partial) < ξ(none): {xi_B:.4f} vs {xi_C:.4f}"
    )

    # Rank-level agreement: Spearman(recall, -ξ) should be strongly positive
    recalls = [recall_A, recall_B, recall_C]
    neg_xi = [-xi_A, -xi_B, -xi_C]
    rho = _spearman(recalls, neg_xi)
    assert rho > 0.8, f"Expected strong positive rank correlation; got ρ={rho:.3f}"

    # Determinism: compute_xi should be stable on repeated calls for same text
    assert compute_xi(post_A) == pytest.approx(xi_A, abs=1e-9)
    assert compute_xi(post_B) == pytest.approx(xi_B, abs=1e-9)
    assert compute_xi(post_C) == pytest.approx(xi_C, abs=1e-9)