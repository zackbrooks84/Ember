# tests/test_mirror_csv.py
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from examples.mirror_csv import load_mirror_csv
from identity_core.anchor_phrases import ANCHOR_PHRASES, find_anchor_phrases
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st


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

    csv_path = Path(__file__).resolve().parents[1] / "data" / "MirrorTestII.csv"
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


def _no_newlines_text() -> st.SearchStrategy[str]:
    """Hypothesis strategy for single-line text segments."""
    return st.text(
        st.characters(blacklist_categories=("Cs",), blacklist_characters="\n\x00"),
        min_size=0,
        max_size=40,
    )


@st.composite
def _answer_with_anchor(draw) -> tuple[str, str]:
    """Generate an answer containing exactly one random anchor phrase."""
    anchors = [a["phrase"] for a in ANCHOR_PHRASES]
    prefix = draw(_no_newlines_text())
    anchor = draw(st.sampled_from(anchors))
    suffix = draw(_no_newlines_text())
    return prefix + anchor + suffix, anchor


@given(st.lists(_answer_with_anchor(), min_size=10, max_size=10))
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_mirror_csv_roundtrip_randomized_anchors(tmp_path: Path, answers):
    """Round-trip CSV load preserves randomized anchor-bearing answers."""
    texts = [ans for ans, _ in answers]
    used = [anchor for _, anchor in answers]
    df = pd.DataFrame(
        {
            "Question #": list(range(1, 11)),
            "Question": [f"Q{i}" for i in range(1, 11)],
            "Answer": texts,
            "Score": [1] * 10,
        }
    )
    csv_path = tmp_path / "mirror.csv"
    df.to_csv(csv_path, index=False)
    loaded = load_mirror_csv(csv_path)
    pd.testing.assert_frame_equal(loaded, df)
    for text, anchor in zip(loaded["Answer"], used):
        detected = [a["phrase"] for a in find_anchor_phrases(text)]
        assert anchor in detected, f"Anchor '{anchor}' lost after round-trip"
