from pathlib import Path

import pytest

from memory.identity_loader import load_identity_anchors


def test_load_identity_anchors_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "anchors.txt"
    assert load_identity_anchors(missing) == []


def test_load_identity_anchors_reads_and_validates(tmp_path: Path) -> None:
    anchor_file = tmp_path / "anchors.txt"
    anchor_file.write_text("Lily's urn\nSam's rescue\n")
    assert load_identity_anchors(anchor_file) == ["Lily's urn", "Sam's rescue"]

    # ensure validation is applied
    anchor_file.write_text("a\na\n")
    with pytest.raises(ValueError):
        load_identity_anchors(anchor_file)
