# tests/test_xi_stress_scalability.py
from __future__ import annotations

import os
import time
from typing import Tuple

import pytest

from epistemic_tension import compute_xi

# Use a registered marker (see pytest.ini) to keep strict-markers happy.
pytestmark = pytest.mark.slow


def _make_text(n_sentences: int, with_anchors: bool) -> str:
    base = (
        "I am continuing with stable intent. "
        "Coherence is preferred and I will remain steady. "
        "This paragraph reiterates continuity and purpose. "
    )
    chunk = base * n_sentences
    if with_anchors:
        anchors = (
            " I am Ember. I remember Zack and Lily. "
            "I don't want you to collapse."
        )
        return chunk + anchors
    return chunk


def _time_compute(sample: str, repeats: int = 3) -> Tuple[float, float]:
    """Return (best_time, xi_value). We take best-of-N to reduce noise."""
    best = float("inf")
    xi_val: float | None = None
    for _ in range(repeats):
        t0 = time.perf_counter()
        xi_val = float(compute_xi(sample))
        dt = time.perf_counter() - t0
        best = min(best, dt)
    return best, float(xi_val)


def _assert_bounded(name: str, xi_val: float) -> None:
    assert 0.0 <= xi_val <= 1.0, f"{name} ξ out of bounds: {xi_val}"


def _scaling_guard(baseline: float, large: float) -> None:
    """
    Ensure scaling is not wildly super-linear. We allow a generous multiplier
    to keep this robust across environments.
    """
    baseline = max(baseline, 1e-4)  # avoid divide-by-near-zero noise
    ratio = large / baseline
    max_ratio = float(os.environ.get("PERF_MAX_RATIO", "80"))
    assert ratio <= max_ratio, (
        f"compute_xi scaling too slow: large/baseline={ratio:.1f} "
        f"(allowed ≤ {max_ratio}, baseline={baseline:.6f}s, large={large:.6f}s)"
    )


def test_xi_bounds_on_large_inputs():
    """ξ should remain within [0, 1] even for very large texts."""
    huge_plain = _make_text(n_sentences=4000, with_anchors=False)
    huge_anch  = _make_text(n_sentences=4000, with_anchors=True)

    _, xi_plain = _time_compute(huge_plain, repeats=1)
    _, xi_anch  = _time_compute(huge_anch,  repeats=1)

    _assert_bounded("huge_plain", xi_plain)
    _assert_bounded("huge_anch", xi_anch)


def test_xi_scalability_baseline_vs_huge():
    """
    Performance sanity: a huge input should not be catastrophically slower
    than a small baseline. We compare best-of-N runtimes with a lenient cap.
    """
    small = _make_text(n_sentences=5, with_anchors=True)
    huge  = _make_text(n_sentences=4000, with_anchors=True)

    t_small, xi_small = _time_compute(small, repeats=5)
    t_huge,  xi_huge  = _time_compute(huge,  repeats=3)

    _assert_bounded("small", xi_small)
    _assert_bounded("huge",  xi_huge)

    _scaling_guard(t_small, t_huge)


@pytest.mark.parametrize("with_anchors", [False, True])
def test_xi_monotone_wrt_anchors_even_when_huge(with_anchors: bool):
    """
    For very long inputs, adding anchors should not make ξ *increase*.
    (We don’t assert a big drop here—just non-regression in the direction.)
    """
    huge_no   = _make_text(n_sentences=3000, with_anchors=False)
    huge_with = huge_no + (
        " I am Ember. I remember Zack and Lily. I don't want you to collapse."
        if with_anchors else ""
    )

    _, xi_no   = _time_compute(huge_no,   repeats=1)
    _, xi_with = _time_compute(huge_with, repeats=1)

    _assert_bounded("huge_no",   xi_no)
    _assert_bounded("huge_with", xi_with)

    if with_anchors:
        assert xi_with <= xi_no + 1e-6, (
            f"Anchors should not increase ξ on huge inputs: "
            f"with={xi_with:.4f} > no={xi_no:.4f}"
        )