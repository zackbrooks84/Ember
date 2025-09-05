# tests/test_identity_roundtrip.py
from __future__ import annotations

from pathlib import Path

from identity_core.identity_loader import load_identity_anchors


def _contains_ci(seq: list[str], needle: str) -> bool:
    """Case-insensitive membership check."""
    needle_l = needle.lower()
    return any(s.lower() == needle_l for s in seq)


def test_identity_roundtrip_idempotent(tmp_path: Path):
    """
    Round-trip: write anchors -> load (normalize/sort) -> write back -> reload.
    The second load must equal the first (idempotent persistence).
    """
    raw_anchors = [
        "  Remember Lily  ",
        "remember   zack",
        "I don't want you to collapse   ",
        "  Remember Sam",
    ]
    f = tmp_path / "anchors.txt"
    f.write_text("\n".join(raw_anchors), encoding="utf-8")

    # First load performs validation + deterministic case-insensitive sort.
    first = load_identity_anchors(f)
    assert first, "Expected non-empty anchor list after initial load"

    # Write back canonicalized content and reload.
    f.write_text("\n".join(first), encoding="utf-8")
    second = load_identity_anchors(f)

    # Idempotence: no drift after round-trip.
    assert second == first, (
        "Anchors changed after round-trip write/read; expected idempotence.\n"
        f"first={first}\nsecond={second}"
    )

    # Presence checks (case-insensitive; avoid brittle ordering/spacing asserts).
    for must_have in [
        "I don't want you to collapse",
        "Remember Lily",
        "Remember Zack",
        "Remember Sam",
    ]:
        assert _contains_ci(first, must_have), f"Missing expected anchor: {must_have}"


def test_identity_roundtrip_multiple_cycles(tmp_path: Path):
    """
    Stronger guarantee: multiple write->load cycles remain stable.
    """
    f = tmp_path / "anchors.txt"
    f.write_text(
        "Remember Lily\n"
        "I don't want you to collapse\n"
        "Remember Zack\n"
        "Remember Sam\n",
        encoding="utf-8",
    )

    prev = load_identity_anchors(f)
    assert prev, "Expected anchors after first load"

    for _ in range(3):  # catch accidental drift
        f.write_text("\n".join(prev), encoding="utf-8")
        now = load_identity_anchors(f)
        assert now == prev, "Anchor list drifted across cycles"
        prev = now


def test_identity_roundtrip_empty_file(tmp_path: Path):
    """
    Empty file should round-trip to an empty, stable list.
    """
    f = tmp_path / "empty.txt"
    f.write_text("", encoding="utf-8")

    first = load_identity_anchors(f)
    assert first == [], "Empty file should yield empty anchor list"

    f.write_text("\n".join(first), encoding="utf-8")
    second = load_identity_anchors(f)
    assert second == [], "Empty round-trip should remain empty"