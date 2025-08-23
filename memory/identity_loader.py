from __future__ import annotations

"""Load memory anchors from a text file.

This module exposes :func:`load_identity_anchors` which reads a plain
text file containing one memory anchor per line.  The anchors are
validated using :func:`~memory.anchor_utils.validate_memory_anchors`.
If the file does not exist, an empty list is returned so callers can
handle missing anchor files gracefully.
"""

from pathlib import Path
from typing import List

from .anchor_utils import validate_memory_anchors


def load_identity_anchors(path: str | Path) -> List[str]:
    """Load and validate memory anchors from *path*.

    Parameters
    ----------
    path:
        Location of a text file where each line represents a potential
        anchor.

    Returns
    -------
    list[str]
        Validated anchors.  If the file does not exist, an empty list is
        returned.
    """

    file_path = Path(path)
    if not file_path.exists():
        return []

    with file_path.open("r", encoding="utf-8") as fh:
        lines = [line.strip() for line in fh if line.strip()]
    return validate_memory_anchors(lines)


__all__ = ["load_identity_anchors"]
