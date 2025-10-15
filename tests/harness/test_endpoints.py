# tests/harness/test_endpoints.py
import numpy as np
from harness.metrics import (
    xi_series, k_window_lvs, anchor_vector,
    anchor_persistence, ewma, lock_detect
)

def test_lock_detect_smoke():
    # Synthetic embeddings that stabilize late
    rng = np.random.default_rng(0)
    T, d = 40, 16
    E = rng.normal(size=(T, d))

    # Force the last 12 turns to align near an anchor (stability)
    anchor = rng.normal(size=(d,))
    anchor /= np.linalg.norm(anchor)
    for t in range(T - 12, T):
        E[t] = anchor + 0.01 * rng.normal(size=(d,))

    # Metrics
    xi = xi_series(E)             # (T-1,)
    lvs = k_window_lvs(E, k=5)    # (T,)
    a = anchor_vector(E, n_seed=3)
    Pt = anchor_persistence(E, a)
    xi_s = ewma(xi, alpha=0.5)

    # Basic expectations for a stabilizing series
    assert np.median(xi[-10:]) < 0.05
    assert lock_detect(xi, lvs[-1], eps_xi=0.05, eps_lvs=0.02, m=5)
    assert Pt[-1] > Pt[5]
    assert xi_s[-1] <= xi[-1] + 1e-9  # EWMA is smoothed, not exploding
