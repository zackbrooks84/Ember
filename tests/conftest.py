import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure the repository root (one level up from ``tests``) is on the
# import path.  This allows the test suite to import project modules
# without depending on the current working directory used when invoking
# ``pytest``.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configure the flame log path before test modules import the logging code.
LOG_PATH = Path(tempfile.gettempdir()) / "flame.log"
os.environ["FLAME_LOG"] = str(LOG_PATH)


@pytest.fixture(scope="session", autouse=True)
def flame_log(tmp_path_factory):
    """Configure the flame log file for the test session."""
    # The environment variable is set at import time above; simply expose the
    # chosen path for the test run.
    yield
    print(f"Flame log written to {LOG_PATH}")
