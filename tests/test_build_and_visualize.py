import os
from pathlib import Path

import pandas as pd
import pytest
import rich_click as click

os.environ.setdefault("MPLBACKEND", "Agg")

from gantty.gantty import _parse_after_reference, build, buildCD, visualize


class DummyCtx:
    def __init__(self):
        self.called = False

    def exit(self):
        self.called = True
        raise click.exceptions.Exit()


def write_csv(path: Path, rows, header=("Label", "Task", "Session", "Start", "Durate")):
    content = [",".join(header)]
    for row in rows:
        content.append(",".join(str(value) for value in row))
    path.write_text("\n".join(content), encoding="utf-8")


def test_buildCD_cycles_colors():
    sessions = [f"S{i}" for i in range(7)]
    cdict = buildCD(sessions)
    assert cdict["S0"] == cdict["S5"]
    assert set(cdict) == set(sessions)


def test_parse_after_reference_variants():
    assert _parse_after_reference("after TaskA") == "TaskA"
    assert _parse_after_reference("After Task B") == "Task B"
    assert _parse_after_reference("2025-01-01") is None


def test_build_success_with_dependency_resolution_out_of_order(tmp_path):
    csv_path = tmp_path / "plan.csv"
    write_csv(
        csv_path,
        [
            ("C", "Task C", "S2", "after B", "1d"),
            ("A", "Task A", "S1", "2025-01-01", "2d"),
            ("B", "Task B", "S1", "after A", "3d"),
        ],
    )

    df = build(DummyCtx(), csv_path, show=False)

    assert list(df["Label"]) == ["C", "A", "B"]
    row_a = df[df["Label"] == "A"].iloc[0]
    row_b = df[df["Label"] == "B"].iloc[0]
    row_c = df[df["Label"] == "C"].iloc[0]

    assert row_b["Start_Values"] == row_a["End"]
    assert row_c["Start_Values"] == row_b["End"]
    assert all(df["color"].notna())


def test_build_show_calls_context_exit(tmp_path):
    csv_path = tmp_path / "plan.csv"
    write_csv(csv_path, [("A", "Task A", "S1", "2025-01-01", "1d")])
    ctx = DummyCtx()

    with pytest.raises(click.exceptions.Exit):
        build(ctx, csv_path, show=True)

    assert ctx.called is True


def test_build_raises_for_missing_columns(tmp_path):
    csv_path = tmp_path / "missing.csv"
    write_csv(csv_path, [("A", "Task A", "2025-01-01", "1d")], header=("Label", "Task", "Start", "Durate"))

    with pytest.raises(click.ClickException, match="Missing required CSV columns"):
        build(DummyCtx(), csv_path, show=False)


def test_build_raises_for_invalid_duration(tmp_path):
    csv_path = tmp_path / "invalid_duration.csv"
    write_csv(csv_path, [("A", "Task A", "S1", "2025-01-01", "bad")])

    with pytest.raises(click.ClickException, match="Invalid duration format"):
        build(DummyCtx(), csv_path, show=False)


def test_build_raises_for_invalid_start_value(tmp_path):
    csv_path = tmp_path / "invalid_start.csv"
    write_csv(csv_path, [("A", "Task A", "S1", "tomorrow maybe", "1d")])

    with pytest.raises(click.ClickException, match="Invalid start value"):
        build(DummyCtx(), csv_path, show=False)


def test_build_raises_for_unresolved_dependencies(tmp_path):
    csv_path = tmp_path / "unresolved.csv"
    write_csv(
        csv_path,
        [
            ("A", "Task A", "S1", "after B", "1d"),
            ("B", "Task B", "S1", "after A", "1d"),
        ],
    )

    with pytest.raises(click.ClickException, match="Cannot resolve"):
        build(DummyCtx(), csv_path, show=False)


def _sample_df_for_visualize():
    return pd.DataFrame(
        {
            "Label": ["A", "B"],
            "Task": ["Task A", "Task B"],
            "Session": ["S1", "S2"],
            "Start_Values": pd.to_datetime(["2025-01-01", "2025-01-03"]),
            "End": pd.to_datetime(["2025-01-03", "2025-01-06"]),
            "Start_Num": [0, 2],
            "End_Num": [2, 5],
            "Day_Start_2_End": [2, 3],
            "color": ["#E64646", "#E69646"],
        }
    )


def test_visualize_raises_on_empty_df():
    with pytest.raises(click.ClickException, match="no rows"):
        visualize(pd.DataFrame())


def test_visualize_saves_file(tmp_path):
    out = tmp_path / "gantt.png"
    visualize(_sample_df_for_visualize(), outputFile=out, display=False, step=0, no_sessions=False)
    assert out.exists()
    assert out.stat().st_size > 0


def test_visualize_display_calls_show(monkeypatch):
    calls = {"show": 0}

    def fake_show():
        calls["show"] += 1

    monkeypatch.setattr("gantty.gantty.plt.show", fake_show)
    visualize(_sample_df_for_visualize(), display=True, no_sessions=True)
    assert calls["show"] == 1
