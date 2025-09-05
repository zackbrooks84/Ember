#!/usr/bin/env python3
"""Generate a markdown table of public functions and their docstrings.

This script introspects the ``identity_core`` package, collects public
functions defined in each module, and prints a markdown table with the
function name, source module, and the first line of the function's
docstring. Modules that fail to import are skipped.

Usage:
    python docs/generate_function_table.py > table.md
"""
from __future__ import annotations

import importlib
import inspect
import pkgutil
import pathlib
import sys
from typing import Iterable, List, Tuple

# Ensure repository root is on the import path when executed from /docs
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

PACKAGE = "identity_core"


def iter_public_functions() -> Iterable[Tuple[str, str, str]]:
    """Yield tuples of (name, module_name, first_line_of_docstring)."""
    pkg = importlib.import_module(PACKAGE)
    package_path = pathlib.Path(pkg.__file__).parent
    for info in pkgutil.iter_modules([str(package_path)]):
        if info.name.startswith("_"):
            continue
        try:
            mod = importlib.import_module(f"{PACKAGE}.{info.name}")
        except Exception as exc:  # pragma: no cover - skip problematic modules
            print(f"skip {info.name}: {exc}", file=sys.stderr)
            continue
        public = getattr(mod, "__all__", None)
        names: Iterable[str]
        if public is None:
            names = [n for n in dir(mod) if not n.startswith("_")]
        else:
            names = public
        for name in names:
            obj = getattr(mod, name, None)
            if inspect.isfunction(obj):
                doc = inspect.getdoc(obj) or ""
                first = doc.strip().splitlines()[0] if doc else ""
                yield name, info.name, first


def build_table(rows: Iterable[Tuple[str, str, str]]) -> str:
    lines: List[str] = ["| Function | Module | Description |", "|---------|--------|-------------|"]
    for name, mod, desc in sorted(rows, key=lambda x: (x[1], x[0])):
        lines.append(f"| `{name}` | `{mod}` | {desc} |")
    return "\n".join(lines)


if __name__ == "__main__":
    print(build_table(iter_public_functions()))
