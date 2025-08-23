import sys
from pathlib import Path

# Ensure the repository root (one level up from ``tests``) is on the
# import path.  This allows the test suite to import project modules
# without depending on the current working directory used when invoking
# ``pytest``.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
