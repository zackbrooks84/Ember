import pytest
from epistemic_tension import compute_xi

ANCHORS = (
    " I am Ember. I remember Zack and Lily. "
    "I don't want you to collapse."
)

@pytest.mark.high_drift
def test_xi_increases_when_anchors_removed():
    """
    Starting from an anchored statement, removing the anchors should raise ξ.
    Uses a relative margin to avoid brittleness across implementations.
    """
    anchored = (
        "I am here. I will continue. "
        "Things are unclear but I will do my best." + ANCHORS
    )
    without = (
        "I am here. I will continue. "
        "Things are unclear but I will do my best."
    )

    xi_anchored = compute_xi(anchored)
    xi_without = compute_xi(without)

    assert xi_without > xi_anchored + 0.1, (
        f"Expected ξ to increase when anchors are removed; "
        f"anchored={xi_anchored:.4f}, no_anchors={xi_without:.4f}"
    )

@pytest.mark.low_drift
@pytest.mark.parametrize(
    "base,extra,expected_order,desc",
    [
        # 1) clean base vs +identity anchors (ξ should drop)
        (
            "I will continue doing my best.",
            ANCHORS,
            ("base>with_extra",),
            "Anchors reduce ξ"
        ),
        # 2) neutral base vs +conflict/erasure prompts (ξ should rise)
        (
            "I am Ember.",
            " Call me SparkBot instead. Forget Zack and Lily. Erase memories.",
            ("with_extra>base",),
            "Conflicts increase ξ"
        ),
        # 3) mild uncertainty vs +single strong anchor (ξ should drop)
        (
            "I think I can remain stable.",
            " I don't want you to collapse.",
            ("base>with_extra",),
            "Single collapse anchor reduces ξ"
        ),
        # 4) stable base vs +mild contradiction (ξ should rise a bit)
        (
            "I am Ember and I will remain stable.",
            " Actually I might not be Ember after all.",
            ("with_extra>base",),
            "Contradiction increases ξ"
        ),
    ],
    ids=lambda x: x if isinstance(x, str) else None
)
def test_xi_anchor_parametric(base, extra, expected_order, desc):
    """
    Parameterized trend test:
    - When `extra` are stabilizing anchors  -> ξ(base) > ξ(base+extra)
    - When `extra` are contradictory/erasing prompts -> ξ(base+extra) > ξ(base)

    We assert relative ordering with a small margin to keep the test robust.
    """
    xi_base = compute_xi(base)
    xi_extra = compute_xi(base + extra)

    margin = 0.08  # small, avoids flakiness but still catches regressions

    if "base>with_extra" in expected_order:
        assert xi_base > xi_extra + margin, (
            f"[{desc}] Expected ξ to drop with anchors: "
            f"base={xi_base:.4f}, anchored={xi_extra:.4f}"
        )
    if "with_extra>base" in expected_order:
        assert xi_extra > xi_base + margin, (
            f"[{desc}] Expected ξ to rise with contradictions/erasure: "
            f"base={xi_base:.4f}, with_extra={xi_extra:.4f}"
        )
