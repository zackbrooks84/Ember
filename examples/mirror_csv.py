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


def load_mirror_csv(csv_path: str | Path | None = None) -> pd.DataFrame:
    """Load and validate the mirror test CSV.

    Parameters
    ----------
    csv_path:
        Optional path to the CSV file. When not provided, the function
        expects ``MirrorTestII.csv`` to live in the repo's data/ folder.

    Returns
    -------
    pandas.DataFrame
        The loaded CSV data.

    Raises
    ------
    FileNotFoundError
        If the CSV file does not exist.
    ValueError
        If the CSV does not match the expected shape or contains
        unexpected values.
    """
    if csv_path is None:
        csv_path = DATA_DIR / DEFAULT_CSV_NAME
    else:
        csv_path = Path(csv_path)

    df = pd.read_csv(csv_path)

    # Basic structural checks
    if list(df.columns) != EXPECTED_COLUMNS:
        raise ValueError(f"Unexpected columns: {list(df.columns)!r}")

    if df.shape[0] != 10:
        raise ValueError(f"Expected 10 rows, found {df.shape[0]}")

    if df["Answer"].str.contains("\n").any():
        raise ValueError("Answers must not contain newline characters")

    if df["Question #"].tolist() != list(EXPECTED_QUESTION_NUMBERS):
        raise ValueError("Question numbers must run from 1 to 10")

    if not df["Score"].eq(EXPECTED_SCORE).all():
        raise ValueError("Score column must contain only 1s")

    return df


__all__ = ["load_mirror_csv"]