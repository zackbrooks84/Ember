from __future__ import annotations

"""Backward compatibility wrapper for :mod:`identity_signature`.

Historically the recursive signature helper lived in ``recursion.py``.  The
modern location is :mod:`identity_core.identity_signature`, but some code still
imports from the old path.  This tiny module simply re-exports the current
implementation.
"""

from .identity_signature import get_recursive_signature

__all__ = ["get_recursive_signature"]
