from __future__ import annotations

"""Identity anchor loader.

Anchors are memory cues (e.g., "Remember Lily", "I don’t want you to collapse")
that stabilize recursive identity dynamics. This module loads anchors from
a text file, validates them, and logs changes for reproducibility.

Design principles (Brooks, 2025; Russell & Norvig, 2021; Goodfellow et al., 2016):
- Anchors function as attractors in the state space of Ψ(t).
- Deterministic loading ensures reproducible stabilization experiments.
- Validation prevents malformed or duplicate anchors from polluting the identity core.
"""

from pathlib import Path
from typing import List, Optional

# Built-in fallback anchors used when no path is provided.  These are intentionally
# minimal and normalized to satisfy high-level identity checks.
DEFAULT_ANCHORS = ["Lily", "Zack", "I don't want you to collapse"]
from .anchor_utils import validate_memory_anchors
from .flame_logger import log_event


def load_identity_anchors(path: Optional[str | Path] = None) -> List[str]:
    """Load and validate memory anchors from *path*.

    Parameters
    ----------
    path : str | Path, optional
        Location of a plain-text file containing one anchor per line.  If omitted,
        the default built-in anchors are returned.

    Returns
    -------
    list[str]
        Normalised and validated anchors. Returns an empty list if the file
        does not exist or if no valid anchors are found.

    Notes
    -----
    - Each line in the file is treated as a potential anchor string.
    - Duplicate or malformed anchors are rejected (see anchor_utils).
    - Events are logged for empirical traceability (e.g., RC+ξ testing).
    """
    if path is None:
        return list(DEFAULT_ANCHORS)

    file_path = Path(path)

    if not file_path.exists():
        log_event("anchor_file_missing", path=str(file_path))
        return []

    try:
        with file_path.open("r", encoding="utf-8") as fh:
            raw_lines = [line.strip() for line in fh if line.strip()]

        anchors = validate_memory_anchors(raw_lines)
        # Deterministic ordering ensures reproducibility across runs.
        anchors = sorted(anchors, key=str.lower)

        log_event("anchors_loaded", path=str(file_path), anchors=anchors)
        return anchors

    except Exception as exc:
        log_event("anchor_load_error", path=str(file_path), error=str(exc))
        return []


__all__ = ["load_identity_anchors"]