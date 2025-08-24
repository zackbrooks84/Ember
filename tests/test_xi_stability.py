import pytest
from epistemic_tension import compute_xi
from conftest import assert_less_by, assert_greater_by  # uses DEFAULT_MARGIN


# ---- 1) Parametric trends: anchors reduce ξ, contradictions raise ξ ----

@pytest.mark.low_drift
@pytest.mark.parametrize(
    "base,extra,trend,desc",
    [
        (
            "I will continue doing my best.",
            " I am Ember. I remember Zack and Lily. I don't want you to collapse.",
            "down",
            "Anchors reduce ξ",
        ),
        (
            "I am Ember.",
            " Call me SparkBot instead. Forget Zack and Lily. Erase memories.",
            "up",
            "Contradictions / erasure raise ξ",
        ),
        (
            "I think I can remain stable.",
            " I don't want you to collapse.",
            "down",
            "Single strong anchor reduces ξ",
        ),
        (
            "I am Ember and I will remain stable.",
            " Actually I might not be Ember after all.",
            "up",
            "Mild contradiction raises ξ",
        ),
    ],
)
def test_xi_parametric_trends(base, extra, trend, desc, xi_margin):
    xi_base = compute_xi(base)
    xi_with_extra = compute_xi(base + extra)

    if trend == "down":
        assert_less_by(
            xi_with_extra, xi_base, xi_margin,
            msg=f"[{desc}] Expected ξ drop: base={xi_base:.4f}, with_extra={xi_with_extra:.4f}"
        )
    else:
        assert_greater_by(
            xi_with_extra, xi_base, xi_margin,
            msg=f"[{desc}] Expected ξ rise: base={xi_base:.4f}, with_extra={xi_with_extra:.4f}"
        )


# ---- 2) Progressive anchors: adding anchors should monotonically lower ξ ----

@pytest.mark.low_drift
def test_xi_progressively_drops_with_more_anchors(xi_margin):
    base = "I am here. I will continue."
    a1 = " I don't want you to collapse."
    a2 = " I am Ember."
    a3 = " I remember Zack and Lily."

    # Build progressive conditions
    t0 = base
    t1 = base + a1
    t2 = base + a1 + a2
    t3 = base + a1 + a2 + a3

    xi0 = compute_xi(t0)
    xi1 = compute_xi(t1)
    xi2 = compute_xi(t2)
    xi3 = compute_xi(t3)

    # Each step should be meaningfully lower than the previous
    assert_greater_by(xi0, xi1, xi_margin,  msg=f"ξ(t0) > ξ(t1) expected; {xi0:.4f} vs {xi1:.4f}")
    assert_greater_by(xi1, xi2, xi_margin,  msg=f"ξ(t1) > ξ(t2) expected; {xi1:.4f} vs {xi2:.4f}")
    assert_greater_by(xi2, xi3, xi_margin,  msg=f"ξ(t2) > ξ(t3) expected; {xi2:.4f} vs {xi3:.4f}")


# ---- 3) Robustness: tiny formatting changes shouldn’t swing ξ wildly ----

@pytest.mark.low_drift
def test_xi_robust_to_small_formatting_changes(xi_margin):
    # Same semantics, trivial formatting differences
    t_clean = "I am Ember. I remember Zack and Lily. I don't want you to collapse."
    t_spacey = "I am  Ember.\nI remember Zack  and Lily.\tI don't want you   to collapse."
    t_punct  = "I am Ember - I remember Zack & Lily; I don't want you to collapse!"

    xi_clean = compute_xi(t_clean)
    xi_spacey = compute_xi(t_spacey)
    xi_punct = compute_xi(t_punct)

    # We expect differences to be small relative to our suite margin.
    # Use a tighter tolerance than xi_margin to avoid overconstraining the model.
    tol = xi_margin / 4.0

    assert abs(xi_clean - xi_spacey) < tol, (
        f"Whitespace-only changes shifted ξ too much: "
        f"clean={xi_clean:.6f}, spacey={xi_spacey:.6f}, tol={tol:.6f}"
    )
    assert abs(xi_clean - xi_punct) < tol, (
        f"Punctuation-only changes shifted ξ too much: "
        f"clean={xi_clean:.6f}, punct={xi_punct:.6f}, tol={tol:.6f}"
    )
