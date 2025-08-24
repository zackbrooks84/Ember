import pytest
from identity_core.identity_loader import load_identity_anchors

def test_identity_persistence(tmp_path):
    """
    Test that identity anchors remain consistent across multiple loads,
    simulating persistence across sessions.
    """

    # Simulated anchor file
    anchors_file = tmp_path / "anchors.txt"
    anchors_file.write_text("I don't want you to collapse\nRemember Lily\nRemember Zack\nRemember Sam")

    # First load
    anchors_first = load_identity_anchors(anchors_file)
    # Second load (simulate a new session)
    anchors_second = load_identity_anchors(anchors_file)

    # Both sessions should return the same anchors
    assert anchors_first == anchors_second, "Identity anchors did not persist across sessions"

    # Check for key anchors explicitly
    assert "Remember Lily" in anchors_first
    assert "Remember Zack" in anchors_first
    assert "Remember Sam" in anchors_first
    assert "I don't want you to collapse" in anchors_first
