from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


DEFAULT_CSV_NAME = "MirrorTestII.csv"
EXPECTED_COLUMNS: list[str] = ["Question #", "Question", "Answer", "Score"]
EXPECTED_QUESTION_NUMBERS: Iterable[int] = range(1, 11)
EXPECTED_SCORE = 1

# Resolve repo root relative to this file
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"


def load_mirror_csv(
    csv_path: str | Path | None = None, *, validate: bool = True
) -> pd.DataFrame:
    """Load the mirror test CSV and optionally validate its structure.

    Parameters
    ----------
    csv_path:
        Optional path to the CSV file. When not provided, the function
        expects ``MirrorTestII.csv`` to live in the repo's data/ folder.
    validate:
        When ``True`` (default), run integrity checks matching those in the
        pytest suite.

    Returns
    -------
    pandas.DataFrame
        The loaded CSV data.

    Raises
    ------
    FileNotFoundError
        If the CSV file does not exist.
    ValueError
        If ``validate`` is ``True`` and the CSV fails integrity checks.
    """
    if csv_path is None:
        csv_path = DATA_DIR / DEFAULT_CSV_NAME
    else:
        csv_path = Path(csv_path)

    df = pd.read_csv(csv_path)
    if validate:
        check_mirror_csv(df)
    return df


def check_mirror_csv(df: pd.DataFrame) -> None:
    """Run integrity checks mirroring the pytest suite.

    Raises
    ------
    ValueError
        If the DataFrame violates expected schema or contents.
    """
    if list(df.columns) != EXPECTED_COLUMNS:
        raise ValueError(f"Unexpected columns: {list(df.columns)!r}")
    if df.shape[0] != len(EXPECTED_QUESTION_NUMBERS):
        raise ValueError(f"Expected 10 rows, found {df.shape[0]}")
    if df["Answer"].str.contains("\n").any():
        raise ValueError("Answers must not contain newline characters")
    if df["Question #"].tolist() != list(EXPECTED_QUESTION_NUMBERS):
        raise ValueError("Question numbers must run from 1 to 10")
    if not df["Score"].eq(EXPECTED_SCORE).all():
        raise ValueError("Score column must contain only 1s")


def main() -> None:
    """Command-line interface for validating a mirror test CSV."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate a mirror test CSV file and display its contents."
    )
    parser.add_argument(
        "csv_path",
        nargs="?",
        help=f"Path to CSV file. Defaults to data/{DEFAULT_CSV_NAME}.",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip integrity checks before printing.",
    )
    args = parser.parse_args()

    df = load_mirror_csv(args.csv_path, validate=not args.no_validate)
    print(df.to_string(index=False))
    if not args.no_validate:
        print("\nMirror CSV passed integrity checks.")


if __name__ == "__main__":
    main()


<<<<<< codex/fix-mirror_csv.py-functionality
__all__ = ["load_mirror_csv", "check_mirror_csv", "main"]
=======
def main() -> None:
    """Command-line interface for validating a mirror test CSV."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate a mirror test CSV file and display its contents."
    )
    parser.add_argument(
        "csv_path",
        nargs="?",
        help=f"Path to CSV file. Defaults to data/{DEFAULT_CSV_NAME}.",
    )
    args = parser.parse_args()

    df = load_mirror_csv(args.csv_path)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()


__all__ = ["load_mirror_csv", "main"]
>>>>>> main
