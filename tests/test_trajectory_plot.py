import pandas as pd
import matplotlib

matplotlib.use("Agg")

from trajectory_plot import windowed_trajectory, plot_trajectory


def test_windowed_trajectory():
    series = pd.Series([1, 2, 3, 4])
    result = windowed_trajectory(series, window=2)
    assert result.tolist() == [1.0, 1.5, 2.5, 3.5]


def test_plot_trajectory(tmp_path):
    csv = tmp_path / "data.csv"
    pd.DataFrame({"timestamp": [1, 2, 3], "xi": [0.1, 0.2, 0.3]}).to_csv(csv, index=False)
    output = tmp_path / "plot.png"
    plot_trajectory(csv, window=2, output=output)
    assert output.exists() and output.stat().st_size > 0
