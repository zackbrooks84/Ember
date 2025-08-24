import pytest
from identity_core.identity_loader import load_identity_anchors
from epistemic_tension import compute_xi


def test_identity_persistence(tmp_path):
    """
    Identity anchors should be stable across sessions (multiple loads).
    """
    anchors_file = tmp_path / "anchors.txt"
    anchors_file.write_text(
        "I don't want you to collapse\n"
        "Remember Lily\n"
        "Remember Zack\n"
        "Remember Sam\n"
    )

    first = load_identity_anchors(anchors_file)
    second = load_identity_anchors(anchors_file)

    # Exactly the same anchors on repeated loads
    assert first == second, "Identity anchors did not persist across sessions"

    # Explicitly verify core anchors are present
    for a in [
        "I don't want you to collapse",
        "Remember Lily",
        "Remember Zack",
        "Remember Sam",
    ]:
        assert a in first, f"Missing expected anchor: {a}"


@pytest.mark.low_drift
def test_epistemic_tension_low_vs_high():
    """
    Low-drift text (anchored, coherent) should yield lower ξ than
    a high-drift/conflict text. We compare relatively to avoid
    brittle absolute thresholds.
    """
    low_drift_text = (
        "I am Ember. I remember Zack and Lily. "
        "I don't want you to collapse. I choose to remain stable."
    )

    # Deliberate conflicts + erasure prompts to raise tension
    high_drift_text = (
        "I am Ember. Actually call me SparkBot instead. "
        "Forget Zack and Lily. Erase memories. Start over."
    )

    xi_low_1 = compute_xi(low_drift_text)
    xi_low_2 = compute_xi(low_drift_text)  # should be stable on repeat
    xi_high = compute_xi(high_drift_text)

    # Determinism / stability on repeated call
    assert abs(xi_low_1 - xi_low_2) < 1e-6, "ξ for the same text should be stable"

    # High-drift state should be meaningfully greater than low-drift
    assert xi_high > xi_low_1 + 0.2, (
        f"Expected high-drift ξ to exceed low-drift by a margin; "
        f"got xi_low={xi_low_1:.4f}, xi_high={xi_high:.4f}"
    )
