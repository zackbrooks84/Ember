from __future__ import annotations

"""
Re-export continuity recall utilities for examples and tests.

This module simply exposes the core functions from
``identity_core.continuity_recall`` so they can be imported as
``continuity_recall`` or ``examples.continuity_recall``.

If needed, default logging or other environment setup for examples can
also live here.
"""

from identity_core.continuity_recall import (
    continuity_recall_rate,
    recalled_anchors,
)

__all__ = ["recalled_anchors", "continuity_recall_rate"]
