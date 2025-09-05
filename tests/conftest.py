# tests/conftest.py
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
import random
import json
import contextlib

import numpy as np
import pytest

# -----------------------------------------------------------------------------
# Import path: ensure project root is importable (repo_root/…)
# -----------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# -----------------------------------------------------------------------------
# Determinism: seed PRNGs and (optionally) PYTHONHASHSEED for stable dict order
# -----------------------------------------------------------------------------
# Honor an existing PYTHONHASHSEED if set (pytest may set it). Otherwise default to 0 for stability.
os.environ.setdefault("PYTHONHASHSEED", "0")

SEED = int(os.environ.get("TEST_SEED", "0"))
random.seed(SEED)
np.random.seed(SEED)

# -----------------------------------------------------------------------------
# Flame log location (used by identity_core.flame_logger)
# -----------------------------------------------------------------------------
DEFAULT_FLAME_LOG = Path(tempfile.gettempdir()) / "flame.log"
os.environ.setdefault("FLAME_LOG", str(DEFAULT_FLAME_LOG))

# Default suite-wide margin (can be overridden via --xi-margin)
DEFAULT_MARGIN = 0.08

# -----------------------------------------------------------------------------
# Pytest hooks & CLI options
# -----------------------------------------------------------------------------
def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--xi-margin",
        action="store",
        default=str(DEFAULT_MARGIN),
        help=f"Required difference between WITH and WITHOUT anchors (default={DEFAULT_MARGIN}).",
    )
    parser.addoption(
        "--artifacts-dir",
        action="store",
        default="",
        help="Optional path for writing test artifacts (CSV/JSON). If empty, a tmp dir is used.",
    )


def pytest_configure(config: pytest.Config) -> None:
    # Emit a small banner once for easier CI debugging
    info = {
        "project_root": str(PROJECT_ROOT),
        "flame_log": os.environ.get("FLAME_LOG", ""),
        "seed": SEED,
        "pythonhashseed": os.environ.get("PYTHONHASHSEED", ""),
        "update_golden": os.environ.get("UPDATE_GOLDEN", "0"),
        "xi_margin": config.getoption("--xi-margin"),
    }
    sys.stderr.write("[conftest] session_info: " + json.dumps(info) + "\n")


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def flame_log() -> None:
    """Ensure the flame log file's directory exists and report its location."""
    log_path = Path(os.environ["FLAME_LOG"])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    yield
    # Keep the log for post-run inspection, but print where it is.
    print(f"[conftest] Flame log written to {log_path}")


@pytest.fixture(scope="session")
def artifacts_dir(request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """
    Directory for test artifacts (exports, plots, goldens).
    - Use --artifacts-dir to force a location (e.g., in CI).
    - Otherwise, a session-scoped tmp directory is created.
    """
    user_path = request.config.getoption("--artifacts-dir")
    if user_path:
        p = Path(user_path)
        p.mkdir(parents=True, exist_ok=True)
        return p
    return tmp_path_factory.mktemp("artifacts")


@pytest.fixture
def xi_margin(request: pytest.FixtureRequest) -> float:
    """
    Suite-wide comparison margin for 'WITH anchors < WITHOUT anchors'.
    Can be overridden per-test by passing a value directly.
    """
    try:
        return float(request.config.getoption("--xi-margin"))
    except Exception:
        return DEFAULT_MARGIN


# -----------------------------------------------------------------------------
# Assertion helpers (kept compatible with existing tests)
# -----------------------------------------------------------------------------
def _fmt(v: float) -> str:
    return f"{v:.6f}"

def assert_less_by(lhs: float, rhs: float, delta: float = DEFAULT_MARGIN, msg: str = "") -> None:
    """
    Assert lhs < rhs - delta.
    Example: xi_anchored should be less than xi_base by at least delta.
    """
    if not (lhs < rhs - delta):
        raise AssertionError(msg or f"Expected { _fmt(lhs) } < { _fmt(rhs) } - { _fmt(delta) }")

def assert_greater_by(lhs: float, rhs: float, delta: float = DEFAULT_MARGIN, msg: str = "") -> None:
    """
    Assert lhs > rhs + delta.
    Example: xi_without should be greater than xi_anchored by at least delta.
    """
    if not (lhs > rhs + delta):
        raise AssertionError(msg or f"Expected { _fmt(lhs) } > { _fmt(rhs) } + { _fmt(delta) }")


# Expose helpers for import in tests
__all__ = [
    "assert_less_by",
    "assert_greater_by",
    "xi_margin",
    "artifacts_dir",
]