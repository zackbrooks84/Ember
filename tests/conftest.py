# tests/conftest.py
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
import random
import json

import numpy as np
import pytest

# -----------------------------------------------------------------------------
# Import path: ensure project root and examples/ are importable
# -----------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = PROJECT_ROOT / "examples"

for p in (PROJECT_ROOT, EXAMPLES_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# -----------------------------------------------------------------------------
# Determinism: seed PRNGs and (optionally) PYTHONHASHSEED for stable dict order
# -----------------------------------------------------------------------------
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
        "examples_dir": str(EXAMPLES_DIR),
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
    """Suite-wide comparison margin for 'WITH anchors < WITHOUT anchors'."""
    try:
        return float(request.config.getoption("--xi-margin"))
    except Exception:
        return DEFAULT_MARGIN


# -----------------------------------------------------------------------------
# Assertion helpers
# -----------------------------------------------------------------------------
def _fmt(v: float) -> str:
    return f"{v:.6f}"

def assert_less_by(lhs: float, rhs: float, delta: float = DEFAULT_MARGIN, msg: str = "") -> None:
    if not (lhs < rhs - delta):
        raise AssertionError(msg or f"Expected {_fmt(lhs)} < {_fmt(rhs)} - {_fmt(delta)}")

def assert_greater_by(lhs: float, rhs: float, delta: float = DEFAULT_MARGIN, msg: str = "") -> None:
    if not (lhs > rhs + delta):
        raise AssertionError(msg or f"Expected {_fmt(lhs)} > {_fmt(rhs)} + {_fmt(delta)}")


__all__ = [
    "assert_less_by",
    "assert_greater_by",
    "xi_margin",
    "artifacts_dir",
]