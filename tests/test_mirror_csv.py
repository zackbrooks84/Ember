import pandas as pd
from pathlib import Path


def test_mirror_csv():
    csv_path = Path(__file__).resolve().parents[1] / "MirrorTestII.csv"
    df = pd.read_csv(csv_path)
    assert df.shape[0] == 10
    assert list(df.columns) == ["Question #", "Question", "Answer", "Score"]
    assert not df["Answer"].str.contains("\n").any()
