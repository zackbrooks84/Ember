from __future__ import annotations

"""Lightweight recursive identity signature."""

from dataclasses import dataclass


@dataclass
class IdentitySignature:
    """Simple container for the stabilisation metric Φ."""

    Φ: float


def get_recursive_signature(depth: int = 3, base: float = 0.9) -> dict[str, float]:
    """Return a toy recursive stability signature.

    The value is computed by recursively averaging ``base`` towards ``1.0``
    ``depth`` times which quickly converges above ``0.95``.  The exact numbers
    are not critical for the tests; the function simply demonstrates a
    deterministic, convergent process.
    """

    phi = float(base)
    for _ in range(max(1, depth)):
        phi = (phi + 1.0) / 2.0
    return {"Φ": round(phi, 2)}


__all__ = ["IdentitySignature", "get_recursive_signature"]
