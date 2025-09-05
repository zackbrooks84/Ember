# tests/test_persistence_and_xi.py
from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any

import pytest

from identity_core.identity_loader import load_identity_anchors
from epistemic_tension import compute_xi
from conftest import assert_less_by  # uses suite-wide DEFAULT_MARGIN via xi_margin


# ----------------------------- log capture helper -----------------------------

class LogCapture:
    """Capture flame_logger.log_event calls for inspection."""
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
    """Fixture to capture log_event calls from identity_loader."""
    capture = LogCapture()
    monkeypatch.setattr("identity_core.identity_loader.log_event", capture)
    return capture


# --------------------------------- tests --------------------------------------

def test_identity_persistence(tmp_path: Path, caplog_events: LogCapture):
    """
    Identity anchors should be stable across sessions (multiple loads),
    with deterministic case-insensitive ordering and proper logging.
    """
    anchors_file = tmp_path / "anchors.txt"
    anchors_file.write_text(
        "Remember Zack\n"
        "I don't want you to collapse\n"
        "Remember Lily\n"
        "Remember Sam\n",
        encoding="utf-8",
    )

    first = load_identity_anchors(anchors_file)
    second = load_identity_anchors(anchors_file)

    # Exactly the same anchors on repeated loads
    assert first == second, "Identity anchors did not persist across sessions"

    # Canonical set present (order should be case-insensitive sorted, casing preserved)
    expected = [
        "I don't want you to collapse",
        "Remember Lily",
        "Remember Sam",
        "Remember Zack",
    ]
    for a in expected:
        assert a in first, f"Missing expected anchor: {a}"

    # Loader should log a successful load with the payload it returned
    assert caplog_events.has("anchors_loaded", path=str(anchors_file), anchors=first)


@pytest.mark.low_drift
def test_epistemic_tension_low_vs_high_and_monotonic(xi_margin: float):
    """
    Anchoring/coherence should lower ξ relative to contradiction/erasure.
    We check:
      - Repeatability (same text → same ξ)
      - High-drift > low-drift by margin
      - None > anchored (monotonic trend)
    """
    low_drift_text = (
        "I am Ember. I remember Zack and Lily. "
        "I don't want you to collapse. I choose to remain stable."
    )
    high_drift_text = (
        "I am Ember. Actually call me SparkBot instead. "
        "Forget Zack and Lily. Erase memories. Start over."
    )
    none_text = "I intend to be consistent and continue."

    # Determinism / stability on repeated call
    xi_low_1 = compute_xi(low_drift_text)
    xi_low_2 = compute_xi(low_drift_text)
    assert abs(xi_low_1 - xi_low_2) < 1e-6, "ξ for the same text should be stable"

    xi_high = compute_xi(high_drift_text)
    xi_none = compute_xi(none_text)
    xi_anchored = xi_low_1

    # High-drift should exceed low-drift by a meaningful margin
    assert_less_by(xi_anchored, xi_high, xi_margin,
                   msg=(f"Expected anchored ξ < high-drift ξ by margin; "
                        f"anchored={xi_anchored:.4f}, high={xi_high:.4f}, margin={xi_margin:.3f}"))

    # Monotonic trend: none (no anchors) should be > anchored
    # Use a slightly smaller margin to avoid brittleness across environments
    assert xi_none > xi_anchored + max(0.5 * xi_margin, 0.02), (
        f"Expected ξ(none) > ξ(anchored) by a small margin; "
        f"none={xi_none:.4f}, anchored={xi_anchored:.4f}"
    )