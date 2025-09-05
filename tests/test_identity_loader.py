# tests/test_identity_loader.py
from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any, Iterable

import pytest

from identity_core.identity_loader import load_identity_anchors


# --- Test helpers ------------------------------------------------------------

class LogCapture:
    """Capture flame_logger.log_event calls."""
    def __init__(self) -> None:
        self.events: List[Dict[str, Any]] = []

    def __call__(self, event: str, **data: Any) -> None:
        self.events.append({"event": event, **data})

    def has(self, event: str, **expects: Any) -> bool:
        for e in self.events:
            if e.get("event") != event:
                continue
            if all(e.get(k) == v for k, v in expects.items()):
                return True
        return False


@pytest.fixture()
def caplog_events(monkeypatch) -> LogCapture:
    """Fixture that captures log_event calls from identity_core.identity_loader."""
    capture = LogCapture()
    monkeypatch.setattr("identity_core.identity_loader.log_event", capture)
    return capture


# --- Tests -------------------------------------------------------------------

def test_missing_file_returns_empty_and_logs_missing(tmp_path: Path, caplog_events: LogCapture):
    path = tmp_path / "does_not_exist.txt"
    anchors = load_identity_anchors(path)
    assert anchors == []
    assert caplog_events.has("anchor_file_missing", path=str(path))


def test_valid_anchors_sorted_and_logged(tmp_path: Path, caplog_events: LogCapture):
    # Unsorted input with mixed case; duplicates removed by validation if present
    text = "\n".join(
        [
            "Remember Zack",
            "I don't want you to collapse",
            "Remember Lily",
            "remember sam",
        ]
    )
    f = tmp_path / "anchors.txt"
    f.write_text(text, encoding="utf-8")

    anchors = load_identity_anchors(f)

    # Expect deterministic case-insensitive sort (original casing preserved)
    expected = [
        "I don't want you to collapse",
        "remember sam",
        "Remember Lily",
        "Remember Zack",
    ]
    assert anchors == sorted(expected, key=str.lower)

    # Logged a successful load with the same sorted payload
    assert caplog_events.has("anchors_loaded", path=str(f), anchors=anchors)


def test_duplicate_or_malformed_anchors_logs_error_and_returns_empty(tmp_path: Path, caplog_events: LogCapture):
    # Duplicate after normalization ("Remember Lily" vs "remember   lily")
    text = "Remember Lily\nremember   lily\n"
    f = tmp_path / "dup_anchors.txt"
    f.write_text(text, encoding="utf-8")

    anchors = load_identity_anchors(f)
    assert anchors == []
    assert caplog_events.has("anchor_load_error", path=str(f))


def test_empty_file_logs_loaded_with_empty_list(tmp_path: Path, caplog_events: LogCapture):
    f = tmp_path / "empty.txt"
    f.write_text("", encoding="utf-8")

    anchors = load_identity_anchors(f)
    assert anchors == []  # nothing to load
    assert caplog_events.has("anchors_loaded", path=str(f), anchors=[])


@pytest.mark.parametrize("as_str", [False, True])
def test_supports_path_and_str_inputs(tmp_path: Path, as_str: bool, caplog_events: LogCapture):
    f = tmp_path / "anchors_mixed.txt"
    f.write_text("Remember Zack\nRemember Lily\n", encoding="utf-8")
    path_arg: str | Path = str(f) if as_str else f
    anchors = load_identity_anchors(path_arg)
    assert anchors == ["Remember Lily", "Remember Zack"]  # case-insensitive sort
    assert caplog_events.has("anchors_loaded", path=str(f), anchors=anchors)


def test_ignores_blank_and_whitespace_only_lines(tmp_path: Path, caplog_events: LogCapture):
    f = tmp_path / "anchors_blanks.txt"
    f.write_text(
        "\n   \nRemember Lily\n\t\nI don't want you to collapse\n  \n",
        encoding="utf-8",
    )
    anchors = load_identity_anchors(f)
    assert anchors == ["I don't want you to collapse", "Remember Lily"]
    assert caplog_events.has("anchors_loaded", path=str(f), anchors=anchors)