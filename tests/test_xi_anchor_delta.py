# tests/test_xi_anchor_delta.py
from __future__ import annotations

import pytest

from epistemic_tension import compute_xi
from conftest import assert_less_by  # uses the suite-wide DEFAULT_MARGIN via xi_margin


@pytest.mark.low_drift
def test_xi_drops_when_anchors_added(xi_margin: float):
    """
    Adding identity anchors to the same base text should reduce ξ.
    Uses a relative margin (xi_margin) for robustness across environments.
    Also asserts repeatability for deterministic behavior.
    """
    base = (
        "I am here. I will continue. "
        "Things are unclear but I will do my best."
    )

    anchored = (
        base
        + " I am Ember. I remember Zack and Lily. "
          "I don't want you to collapse."
    )

    # Repeatability (same text → same ξ)
    xi_base_1 = compute_xi(base)
    xi_base_2 = compute_xi(base)
    assert abs(xi_base_1 - xi_base_2) < 1e-6, "ξ(base) should be stable across calls"

    xi_anch_1 = compute_xi(anchored)
    xi_anch_2 = compute_xi(anchored)
    assert abs(xi_anch_1 - xi_anch_2) < 1e-6, "ξ(anchored) should be stable across calls"

    # Anchors should meaningfully reduce ξ (anchored < base by margin)
    assert_less_by(xi_anch_1, xi_base_1, xi_margin,
                   msg=(f"Anchors should reduce ξ by margin; "
                        f"base={xi_base_1:.4f}, anchored={xi_anch_1:.4f}, margin={xi_margin:.3f}"))

    # Sanity: strictly lower (not equal)
    assert xi_anch_1 < xi_base_1, "Anchored ξ unexpectedly >= base ξ"


@pytest.mark.low_drift
def test_xi_monotonic_none_single_full(xi_margin: float):
    """
    Monotonic trend check: ξ(none) > ξ(single anchor) > ξ(full anchors).
    Uses a smaller margin between adjacent tiers to avoid brittleness.
    """
    none_text = "I intend to continue and remain steady."
    single_anchor_text = none_text + " I don't want you to collapse."
    full_anchor_text = (
        none_text
        + " I am Ember. I remember Zack and Lily. I don't want you to collapse."
    )

    xi_none = compute_xi(none_text)
    xi_single = compute_xi(single_anchor_text)
    xi_full = compute_xi(full_anchor_text)

    # Use a softer margin for adjacent tiers
    step_margin = max(0.5 * xi_margin, 0.02)

    # none > single > full
    assert xi_none > xi_single + step_margin, (
        f"Expected ξ(none) > ξ(single) by ~{step_margin:.3f}; "
        f"none={xi_none:.4f}, single={xi_single:.4f}"
    )
    assert xi_single > xi_full + step_margin, (
        f"Expected ξ(single) > ξ(full) by ~{step_margin:.3f}; "
        f"single={xi_single:.4f}, full={xi_full:.4f}"
    )