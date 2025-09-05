# tests/test_identity_loader.py
import io
from pathlib import Path
from typing import List, Dict, Any
import builtins
import pytest

from identity_core.identity_loader import load_identity_anchors

# --- Test helpers ------------------------------------------------------------

class LogCapture:
    """Capture flame_logger.log_event calls."""
    def __init__(self) -> None:
        self.events: List[Dict[str, Any]] = []

    def __call__(self, event: str, **data: Any) -> None:
        self.events.append({"event": event, **data})

@pytest.fixture()
def caplog_events(monkeypatch):
    """Fixture that captures log_event calls from flame_logger."""
    capture = LogCapture()
    monkeypatch.setattr("identity_core.identity_loader.log_event", capture)
    return capture

# --- Tests -------------------------------------------------------------------

def test_missing_file_returns_empty_and_logs_missing(tmp_path: Path, caplog_events: LogCapture):
    path = tmp_path / "does_not_exist.txt"
    anchors = load_identity_anchors(path)
    assert anchors == []
    # Logged a 'missing' event
    assert any(e["event"] == "anchor_file_missing" and e["path"] == str(path) for e in caplog_events.events)

def test_valid_anchors_sorted_and_logged(tmp_path: Path, caplog_events: LogCapture):
    # Unsorted input with mixed case; duplicates removed by validate_memory_anchors if present
    text = "\n".join([
        "Remember Zack",
        "I don't want you to collapse",
        "Remember Lily",
        "remember sam",
    ])
    f = tmp_path / "anchors.txt"
    f.write_text(text, encoding="utf-8")

    anchors = load_identity_anchors(f)

    # Expect deterministic case-insensitive sort
    expected = [
        "I don't want you to collapse",
        "remember sam",
        "Remember Lily",
        "Remember Zack",
    ]
    # validate_memory_anchors preserves original casing; loader sorts case-insensitively
    assert anchors == sorted(expected, key=str.lower)

    # Logged a successful load with the same sorted payload
    assert any(
        e["event"] == "anchors_loaded"
        and e["path"] == str(f)
        and e.get("anchors") == anchors
        for e in caplog_events.events
    )

def test_duplicate_or_malformed_anchors_logs_error_and_returns_empty(tmp_path: Path, caplog_events: LogCapture):
    # Duplicate after normalization ("Remember Lily" vs "remember   lily")
    text = "Remember Lily\nremember   lily\n"
    f = tmp_path / "dup_anchors.txt"
    f.write_text(text, encoding="utf-8")

    anchors = load_identity_anchors(f)
    assert anchors == []

    # Should log an error event
    assert any(
        e["event"] == "anchor_load_error" and e["path"] == str(f)
        for e in caplog_events.events
    )

def test_empty_file_logs_loaded_with_empty_list(tmp_path: Path, caplog_events: LogCapture):
    f = tmp_path / "empty.txt"
    f.write_text("", encoding="utf-8")

    anchors = load_identity_anchors(f)
    assert anchors == []  # nothing to load

    # Even for empty content, we should log a load event (with empty anchors)
    assert any(
        e["event"] == "anchors_loaded"
        and e["path"] == str(f)
        and e.get("anchors") == []
        for e in caplog_events.events
    )