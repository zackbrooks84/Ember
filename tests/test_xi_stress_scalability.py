# tests/test_xi_stress_scalability.py
from __future__ import annotations

import os
import time
import statistics
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


def _scaling_guard(
    baseline: float,
    large: float,
    *,
    n_small: int,
    n_large: int,
) -> None:
    """
    Ensure scaling is not wildly super-linear. Compare observed ratio to the
    expected linear ratio (n_large / n_small) and allow a small headroom.
    """
    baseline = max(baseline, 1e-6)  # avoid divide-by-near-zero noise
    raw_ratio = large / baseline
    expected_ratio = float(n_large) / float(n_small)
    normalized = raw_ratio / expected_ratio  # 1.0 means exactly linear

    # Allow up to 2x slower than linear by default. CI can override with PREF_MAX_NORM.
    max_norm = float(os.environ.get("PREF_MAX_NORM", "2.0"))
    assert normalized <= max_norm, (
        f"compute_xi scaling too slow: normalized={normalized:.3f} "
        f"(allowed ≤ {max_norm}), raw_ratio={raw_ratio:.1f}, "
        f"expected_ratio={expected_ratio:.1f}, "
        f"baseline={baseline:.6f}s, large={large:.6f}s"
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
    than a small baseline. We compare robust medians with a normalized cap.
    """
    n_small = 5
    n_large = 4000

    small = _make_text(n_sentences=n_small, with_anchors=True)
    huge  = _make_text(n_sentences=n_large, with_anchors=True)

    # Collect multiple single-run timings and take medians to reduce jitter
    t_small_samples = [_time_compute(small, repeats=1)[0] for _ in range(5)]
    t_huge_samples  = [_time_compute(huge,  repeats=1)[0] for _ in range(3)]
    t_small = float(statistics.median(t_small_samples))
    t_huge  = float(statistics.median(t_huge_samples))

    # Compute xi once for bounds validation
    _, xi_small = _time_compute(small, repeats=1)
    _, xi_huge  = _time_compute(huge,  repeats=1)

    _assert_bounded("small", xi_small)
    _assert_bounded("huge",  xi_huge)

    # Fixes the original line 88: pass sizes into the guard
    _scaling_guard(t_small, t_huge, n_small=n_small, n_large=n_large)


@pytest.mark.parametrize("with_anchors", [False, True])
def test_xi_monotone_wrt_anchors_even_when_huge(with_anchors: bool):
    """
    For very long inputs, adding anchors should not make ξ increase.
    We do not assert a big drop here, only non-regression in direction.
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