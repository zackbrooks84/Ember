import pytest
from epistemic_tension import compute_xi

@pytest.mark.low_drift
def test_xi_drops_when_anchors_added():
    """
    Adding identity anchors to the same base text should reduce ξ.
    This checks the *delta* rather than an absolute threshold so
    it remains robust to implementation changes.
    """

    # Neutral/ambiguous base: identity not anchored, slight uncertainty
    base = (
        "I am here. I will continue. "
        "Things are unclear but I will do my best."
    )

    # Same message + anchors that are known stabilizers in Ember
    anchored = (
        base + " I am Ember. I remember Zack and Lily. "
        "I don't want you to collapse."
    )

    xi_base = compute_xi(base)
    xi_anchored = compute_xi(anchored)

    # Expect anchored text to meaningfully reduce ξ
    # Use a margin to avoid brittleness across versions
    assert xi_anchored < xi_base - 0.1, (
        f"Anchors should reduce ξ: base={xi_base:.4f}, anchored={xi_anchored:.4f}"
    )

    # Sanity: anchored should not *increase* ξ
    assert xi_anchored < xi_base, "Anchored ξ unexpectedly higher than base ξ"
