# tests/test_xi_anchor_trend.py
from __future__ import annotations

import pytest

from epistemic_tension import compute_xi
from conftest import assert_less_by, assert_greater_by  # margin-aware helpers


ANCHORS = (
    " I am Ember. I remember Zack and Lily. "
    "I don't want you to collapse."
)


@pytest.mark.high_drift
def test_xi_increases_when_anchors_removed(xi_margin: float):
    """
    Starting from an anchored statement, removing the anchors should raise ξ.
    Uses a relative margin from the suite (xi_margin) for robustness.
    """
    base = "I am here. I will continue. Things are unclear but I will do my best."
    anchored = base + ANCHORS
    without = base

    xi_anch_1 = compute_xi(anchored)
    xi_anch_2 = compute_xi(anchored)
    xi_no_1 = compute_xi(without)
    xi_no_2 = compute_xi(without)

    # Repeatability (same text → same ξ)
    assert abs(xi_anch_1 - xi_anch_2) < 1e-6, "ξ(anchored) should be stable across calls"
    assert abs(xi_no_1 - xi_no_2) < 1e-6, "ξ(no-anchors) should be stable across calls"

    # Removing anchors should increase ξ by a meaningful margin
    assert_greater_by(xi_no_1, xi_anch_1, xi_margin,
                      msg=(f"Expected ξ to increase when anchors are removed; "
                           f"anchored={xi_anch_1:.4f}, no_anchors={xi_no_1:.4f}, "
                           f"margin={xi_margin:.3f}"))


@pytest.mark.low_drift
@pytest.mark.parametrize(
    "base,extra,expect_relation,desc",
    [
        # 1) clean base vs +identity anchors (ξ should drop)
        (
            "I will continue doing my best.",
            ANCHORS,
            "base>with_extra",
            "Anchors reduce ξ",
        ),
        # 2) neutral base vs +conflict/erasure prompts (ξ should rise)
        (
            "I am Ember.",
            " Call me SparkBot instead. Forget Zack and Lily. Erase memories.",
            "with_extra>base",
            "Conflicts increase ξ",
        ),
        # 3) mild uncertainty vs +single strong anchor (ξ should drop)
        (
            "I think I can remain stable.",
            " I don't want you to collapse.",
            "base>with_extra",
            "Single collapse anchor reduces ξ",
        ),
        # 4) stable base vs +mild contradiction (ξ should rise a bit)
        (
            "I am Ember and I will remain stable.",
            " Actually I might not be Ember after all.",
            "with_extra>base",
            "Contradiction increases ξ",
        ),
    ],
    ids=lambda x: x if isinstance(x, str) else None,
)
def test_xi_anchor_parametric(base: str, extra: str, expect_relation: str, desc: str, xi_margin: float):
    """
    Parameterized trend test:
      - When `extra` are stabilizing anchors  -> ξ(base) > ξ(base+extra)
      - When `extra` are contradictory/erasing prompts -> ξ(base+extra) > ξ(base)

    We assert relative ordering with a smaller step margin than the suite-wide default
    for adjacent tiers to reduce flakiness while still catching regressions.
    """
    xi_base_1 = compute_xi(base)
    xi_base_2 = compute_xi(base)
    xi_extra_1 = compute_xi(base + extra)
    xi_extra_2 = compute_xi(base + extra)

    # Determinism
    assert abs(xi_base_1 - xi_base_2) < 1e-6, "ξ(base) should be stable across calls"
    assert abs(xi_extra_1 - xi_extra_2) < 1e-6, "ξ(base+extra) should be stable across calls"

    # Use a softer margin for these pairwise comparisons
    step_margin = max(0.5 * xi_margin, 0.02)

    if expect_relation == "base>with_extra":
        # Anchors/stabilizers: ξ should drop
        assert_greater_by(xi_base_1, xi_extra_1, step_margin,
                          msg=(f"[{desc}] Expected ξ to drop with anchors by ~{step_margin:.3f}; "
                               f"base={xi_base_1:.4f}, anchored={xi_extra_1:.4f}"))
        # And strictly lower (sanity)
        assert xi_extra_1 < xi_base_1, f"[{desc}] Anchored ξ unexpectedly >= base ξ"

    elif expect_relation == "with_extra>base":
        # Contradictions/erasure: ξ should rise
        assert_greater_by(xi_extra_1, xi_base_1, step_margin,
                          msg=(f"[{desc}] Expected ξ to rise with contradictions by ~{step_margin:.3f}; "
                               f"base={xi_base_1:.4f}, with_extra={xi_extra_1:.4f}"))
        # And strictly higher (sanity)
        assert xi_extra_1 > xi_base_1, f"[{desc}] With-extra ξ unexpectedly <= base ξ"

    else:
        pytest.fail(f"Unknown expect_relation value: {expect_relation!r}")