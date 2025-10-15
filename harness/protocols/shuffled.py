# harness/protocols/shuffled.py
from __future__ import annotations
import numpy as np
from typing import Optional

def shuffle_embeddings(E: np.ndarray, seed: Optional[int] = 42) -> np.ndarray:
    """
    Return a copy of E with rows randomly permuted.
    Shape preserved; distribution preserved; temporal structure destroyed.
    """
    if E.ndim != 2:
        raise ValueError("E must be 2D (T, d).")
    rng = np.random.default_rng(seed)
    idx = rng.permutation(E.shape[0])
    return E[idx, :]
