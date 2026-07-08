from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import MARKER

from recpipe.cli import main


def run(*argv: str) -> int:
    return main(list(argv))


def test_version(capsys):
    with pytest.raises(SystemExit) as exc:
        run("--version")
    assert exc.value.code == 0
    assert "recpipe" in capsys.readouterr().out


def test_audit_command(dataset: Path, tmp_path: Path, capsys):
    report = tmp_path / "audit.csv"
    code = run("audit", "--input", str(dataset), "--marker", MARKER,
               "--report", str(report))
    out = capsys.readouterr().out
    assert code == 0
    assert "records=39" in out
    assert report.exists()


def test_audit_strict_flags_empty_files(dataset: Path):
    assert run("audit", "--input", str(dataset), "--marker", MARKER, "--strict") == 1


def test_reduce_dry_run_then_apply(dataset: Path, tmp_path: Path, capsys):
    out_dir = tmp_path / "reduced"
    code = run("reduce", "--input", str(dataset), "--output", str(out_dir),
               "--divisor", "5", "--marker", MARKER)
    assert code == 0
    assert "dry run" in capsys.readouterr().out
    assert not out_dir.exists()

    code = run("reduce", "--input", str(dataset), "--output", str(out_dir),
               "--divisor", "5", "--marker", MARKER, "--apply")
    assert code == 0
    assert out_dir.exists()


def test_transform_command(dataset: Path, tmp_path: Path):
    rules = tmp_path / "rules.json"
    rules.write_text(json.dumps({"rules": [{"pattern": r"\bAlice\b", "replacement": "X"}]}))
    out_dir = tmp_path / "transformed"
    code = run("transform", "--input", str(dataset), "--output", str(out_dir),
               "--rules", str(rules), "--marker", MARKER, "--apply")
    assert code == 0
    assert b"Alice" not in (out_dir / "alpha" / "a1.txt").read_bytes()


def test_transform_bad_rules_file_exits_2(dataset: Path, tmp_path: Path, capsys):
    rules = tmp_path / "rules.json"
    rules.write_text(json.dumps({"rules": []}))
    code = run("transform", "--input", str(dataset), "--output", str(tmp_path / "o"),
               "--rules", str(rules), "--marker", MARKER)
    assert code == 2
    assert "error:" in capsys.readouterr().err


def test_validate_command_full_pipeline(dataset: Path, tmp_path: Path, capsys):
    out_dir = tmp_path / "reduced"
    run("reduce", "--input", str(dataset), "--output", str(out_dir),
        "--divisor", "5", "--marker", MARKER, "--apply")
    code = run("validate", "--input", str(dataset), "--output", str(out_dir),
               "--divisor", "5", "--marker", MARKER)
    assert code == 0
    assert "ALL OK" in capsys.readouterr().out


def test_validate_failure_exit_code(dataset: Path, tmp_path: Path):
    out_dir = tmp_path / "reduced"
    run("reduce", "--input", str(dataset), "--output", str(out_dir),
        "--divisor", "5", "--marker", MARKER, "--apply")
    (out_dir / "beta" / "b1.txt").unlink()
    assert run("validate", "--input", str(dataset), "--output", str(out_dir),
               "--divisor", "5", "--marker", MARKER) == 1


def test_reduce_refuses_same_input_output(dataset: Path, capsys):
    code = run("reduce", "--input", str(dataset), "--output", str(dataset),
               "--divisor", "5", "--marker", MARKER, "--apply")
    assert code == 2
    assert "never modified" in capsys.readouterr().err
