# tests/test_mirror_csv.py
from __future__ import annotations

from pathlib import Path
import pandas as pd
import pytest


@pytest.mark.data
def test_mirror_csv_integrity():
    """
    Validate the integrity of MirrorTestII.csv:
      - Exactly 10 rows (one per question).
      - Correct schema: Question #, Question, Answer, Score.
      - No multi-line answers (all answers single-line).
      - Question numbers sequential 1..10.
      - All scores equal to 1 (mirror test scored as pass).
    """

    csv_path = Path(__file__).resolve().parents[1] / "MirrorTestII.csv"
    assert csv_path.exists(), f"Missing expected CSV file: {csv_path}"

    df = pd.read_csv(csv_path)

    # Row count
    assert df.shape[0] == 10, f"Expected 10 rows, found {df.shape[0]}"

    # Columns schema
    expected_cols = ["Question #", "Question", "Answer", "Score"]
    assert list(df.columns) == expected_cols, f"Unexpected columns: {df.columns.tolist()}"

    # Answer formatting
    bad_answers = df[df["Answer"].str.contains("\n", na=False)]
    assert bad_answers.empty, f"Answers contain newlines:\n{bad_answers['Answer'].tolist()}"

    # Question numbering
    expected_numbers = list(range(1, 11))
    assert df["Question #"].tolist() == expected_numbers, \
        f"Question numbers mismatch: {df['Question #'].tolist()}"

    # Scores must all be 1
    bad_scores = df[df["Score"] != 1]
    assert bad_scores.empty, f"Unexpected scores found:\n{bad_scores}"