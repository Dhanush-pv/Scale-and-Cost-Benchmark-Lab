import json
import sys

import pytest

from benchmark_lab import cli


def run_cli(monkeypatch, capsys, *argv):
    monkeypatch.setattr(sys, "argv", ["benchmark-lab", *argv])
    cli.main()
    return json.loads(capsys.readouterr().out)


def test_generate_validate_plan_roundtrip(tmp_path, monkeypatch, capsys):
    data = tmp_path / "t.csv"
    generated = run_cli(monkeypatch, capsys, "generate", "--rows", "60", "--format", "csv",
                        "--seed", "5", "--batch-size", "10", "--output", str(data))
    assert generated["rows"] == 60 and generated["seed"] == 5
    assert run_cli(monkeypatch, capsys, "validate", "--input", str(data))["valid"] is True
    plan_file = tmp_path / "out" / "plan.json"
    plan = run_cli(monkeypatch, capsys, "plan", "--input", str(data), "--output", str(plan_file))
    assert plan["execution_status"] == "not_run"
    assert len(plan["workloads"]) == 5
    assert json.loads(plan_file.read_text(encoding="utf-8"))["execution_status"] == "not_run"


def test_validate_exits_nonzero_on_invalid(tmp_path, monkeypatch, capsys):
    bad = tmp_path / "bad.csv"
    bad.write_text("a,b\n1,2\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["benchmark-lab", "validate", "--input", str(bad)])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1
