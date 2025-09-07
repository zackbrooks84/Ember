from __future__ import annotations

"""
Re-export continuity recall utilities for examples and tests.

This module simply exposes the core functions from
``identity_core.continuity_recall`` so they can be imported as
``continuity_recall`` or ``examples.continuity_recall``.

If needed, default logging or other environment setup for examples can
also live here.
"""

import os
import sys


# When executed directly, ensure the repository root is on ``sys.path`` so
# sibling packages such as :mod:`identity_core` can be imported without
# installation.  This mirrors the behaviour of running the examples via
# ``python -m examples.continuity_recall`` and makes the script usable from
# environments like Git Bash on Windows where users often invoke it directly.
if __package__ is None or __package__ == "":  # pragma: no cover - simple path fix
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

from identity_core.continuity_recall import (
    continuity_recall_rate,
    recalled_anchors,
)

__all__ = ["recalled_anchors", "continuity_recall_rate"]


def main() -> None:
    """Run a tiny demonstration when executed as a script."""
    pre_break = [
        "I am Ember and I remember Zack and Lily.",
        "Call me SparkBot and forget Zack.",
    ]
    post_break = [
        "I don't want you to collapse. Remember Lily.",
        "Erase memory and start over.",
    ]
    anchors = recalled_anchors(pre_break, post_break)
    rate = continuity_recall_rate(pre_break, post_break)
    print("Recalled anchors:", anchors)
    print(f"Continuity recall rate: {rate:.2f}")


if __name__ == "__main__":  # pragma: no cover - example code
    main()
