from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root (which contains examples/) is importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import the actual implementation from examples/
from examples import epistemic_tension as _impl

# Re-export key functions for importers
compute_xi = _impl.compute_xi
normalized_levenshtein = _impl.normalized_levenshtein
interpret_xi = _impl.interpret_xi
cosine_distance = _impl.cosine_distance

XI_SYMBOL = "\u03be"

def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python epistemic_tension.py FILE1 FILE2")

    file1, file2 = map(Path, sys.argv[1:])
    text1 = file1.read_text(encoding="utf-8")
    text2 = file2.read_text(encoding="utf-8")
    xi = normalized_levenshtein(text1, text2)
    label = interpret_xi(xi)
    print(f"{XI_SYMBOL} = {xi:.4f} ({label})")

if __name__ == "__main__":  # pragma: no cover - CLI behavior
    main()
