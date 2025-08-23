from __future__ import annotations

"""Utilities for computing a simple stabilisation sequence.

The original implementation performed naive recursion and recalculated
intermediate results many times.  This refactored version employs
:func:`functools.lru_cache` to memoise previously computed values, greatly
improving performance while retaining a clear recursive interface.
"""

from functools import lru_cache


@lru_cache(maxsize=None)
def stabilization(n: int) -> int:
    """Return the *n*\ -th stabilisation number.

    The sequence is equivalent to the Fibonacci numbers with ``S(0) = 0``
    and ``S(1) = 1``; each subsequent term is the sum of the two
    preceding terms.  Memoisation ensures that each intermediate value is
    only calculated once.

    Parameters
    ----------
    n:
        Index of the desired term.  Must be non-negative.

    Returns
    -------
    int
        The stabilisation number at index ``n``.

    Raises
    ------
    ValueError
        If ``n`` is negative.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if n < 2:
        return n
    return stabilization(n - 1) + stabilization(n - 2)


# A convenient alias expected by some callers.
stabilize = stabilization


__all__ = ["stabilization", "stabilize"]
