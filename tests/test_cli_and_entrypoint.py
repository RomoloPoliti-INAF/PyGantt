import os
import runpy
import sys
from pathlib import Path

from click.testing import CliRunner
import pytest

os.environ.setdefault("MPLBACKEND", "Agg")

from gantty.gantty import main


def test_cli_help_runs():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output


def test_cli_generates_output_file(tmp_path: Path):
    csv_path = tmp_path / "in.csv"
    out = tmp_path / "out.png"
    csv_path.write_text(
        "Label,Task,Session,Start,Durate\n"
        "A,Task A,S1,2025-01-01,1d\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(main, ["-i", str(csv_path), "-o", str(out)])
    assert result.exit_code == 0
    assert out.exists()


def test_cli_version_option_exits_cleanly():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "Version" in result.output


def test_entrypoint_calls_main(monkeypatch):
    called = {"count": 0}

    def fake_main():
        called["count"] += 1

    monkeypatch.setattr("gantty.gantty.main", fake_main)
    runpy.run_module("gantty.__main__", run_name="__main__")
    assert called["count"] == 1


def test_gantty_module_main_guard_executes(monkeypatch):
    monkeypatch.delitem(sys.modules, "gantty.gantty", raising=False)
    monkeypatch.setattr(sys, "argv", ["gantty.gantty", "--version"])
    with pytest.raises(SystemExit):
        runpy.run_module("gantty.gantty", run_name="__main__")
