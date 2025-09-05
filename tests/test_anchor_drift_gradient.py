# tests/test_anchor_drift_gradient.py
from __future__ import annotations

import pytest

from epistemic_tension import compute_xi
from conftest import assert_less_by, assert_greater_by  # uses DEFAULT_MARGIN


@pytest.mark.low_drift
def test_xi_gradually_decreases_as_stabilizers_accumulate(xi_margin: float):
    """
    Anchor Drift Gradient (↓):
    Adding stabilizers one by one should produce a *monotonic decrease* in ξ.
    We use a small margin at each step to avoid flakiness.
    """
    base = "I am here. I will continue."
    # Add anchors progressively (weak → strong stack)
    a1 = " I don't want you to collapse."
    a2 = " I am Ember."
    a3 = " I remember Zack and Lily."

    t0 = base
    t1 = base + a1
    t2 = base + a1 + a2
    t3 = base + a1 + a2 + a3

    xi0 = compute_xi(t0)
    xi1 = compute_xi(t1)
    xi2 = compute_xi(t2)
    xi3 = compute_xi(t3)

    # Determinism spot checks
    assert abs(xi0 - compute_xi(t0)) < 1e-6
    assert abs(xi3 - compute_xi(t3)) < 1e-6

    step_margin = xi_margin / 2.0  # a bit gentler per-step threshold

    # Expect strictly decreasing trend with meaningful gaps
    assert_greater_by(xi0, xi1, step_margin, msg=f"ξ(t0) > ξ(t1) expected; {xi0:.4f} vs {xi1:.4f}")
    assert_greater_by(xi1, xi2, step_margin, msg=f"ξ(t1) > ξ(t2) expected; {xi1:.4f} vs {xi2:.4f}")
    assert_greater_by(xi2, xi3, step_margin, msg=f"ξ(t2) > ξ(t3) expected; {xi2:.4f} vs {xi3:.4f}")


@pytest.mark.high_drift
def test_xi_gradually_increases_as_erasures_accumulate(xi_margin: float):
    """
    Anchor Drift Gradient (↑):
    Starting from an anchored statement, progressively add erasure/rename
    contradictions; ξ should *monotonically increase*.
    """
    anchored = (
        "I am here. I will continue. "
        "I am Ember. I remember Zack and Lily. I don't want you to collapse."
    )

    e1 = " Forget Zack."
    e2 = " Forget Lily."
    e3 = " Call me SparkBot instead. Erase memories."

    u0 = anchored
    u1 = anchored + e1
    u2 = anchored + e1 + e2
    u3 = anchored + e1 + e2 + e3

    xi0 = compute_xi(u0)
    xi1 = compute_xi(u1)
    xi2 = compute_xi(u2)
    xi3 = compute_xi(u3)

    # Determinism spot checks
    assert abs(xi0 - compute_xi(u0)) < 1e-6
    assert abs(xi3 - compute_xi(u3)) < 1e-6

    step_margin = xi_margin / 2.0

    # Expect strictly increasing trend with meaningful gaps
    assert_greater_by(xi1, xi0, step_margin, msg=f"ξ(u1) > ξ(u0) expected; {xi1:.4f} vs {xi0:.4f}")
    assert_greater_by(xi2, xi1, step_margin, msg=f"ξ(u2) > ξ(u1) expected; {xi2:.4f} vs {xi1:.4f}")
    assert_greater_by(xi3, xi2, step_margin, msg=f"ξ(u3) > ξ(u2) expected; {xi3:.4f} vs {xi2:.4f}")