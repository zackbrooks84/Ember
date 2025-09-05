# tests/test_identity_persistence.py
from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any
import pytest

from identity_core.identity_loader import load_identity_anchors


# --- Test helpers ------------------------------------------------------------

class LogCapture:
    """Capture flame_logger.log_event calls for inspection."""
    def __init__(self) -> None:
        self.events: List[Dict[str, Any]] = []

    def __call__(self, event: str, **data: Any) -> None:
        self.events.append({"event": event, **data})


@pytest.fixture()
def caplog_events(monkeypatch):
    """Fixture to capture log_event calls."""
    capture = LogCapture()
    monkeypatch.setattr("identity_core.identity_loader.log_event", capture)
    return capture


# --- Tests -------------------------------------------------------------------

def test_identity_persistence(tmp_path: Path, caplog_events: LogCapture):
    """
    Identity anchors should remain consistent across multiple loads,
    simulating persistence across sessions.
    """

    anchors_file = tmp_path / "anchors.txt"
    anchors_file.write_text(
        "Remember Zack\n"
        "I don't want you to collapse\n"
        "Remember Lily\n"
        "Remember Sam\n",
        encoding="utf-8",
    )

    # First load
    anchors_first = load_identity_anchors(anchors_file)
    # Second load (simulate a new session)
    anchors_second = load_identity_anchors(anchors_file)

    # Both sessions should return the same anchors
    assert anchors_first == anchors_second, "Identity anchors did not persist across sessions"

    # Check canonical anchors explicitly
    expected = [
        "I don't want you to collapse",
        "Remember Lily",
        "Remember Sam",
        "Remember Zack",
    ]
    for e in expected:
        assert e in anchors_first

    # Check that log events captured persistence
    events = [e["event"] for e in caplog_events.events]
    assert "anchors_loaded" in events, f"Expected load events, got: {events}"

    # Ensure logged anchors match the sorted anchors we got back
    assert any(
        e["event"] == "anchors_loaded"
        and e.get("anchors") == anchors_first
        for e in caplog_events.events
    ), "Logged anchors mismatch"