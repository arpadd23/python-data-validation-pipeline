from __future__ import annotations

from pathlib import Path

from conftest import MARKER, make_record

from recpipe.reduce import reduce_tree
from recpipe.validate import validate_tree


def test_validate_after_reduce_ok(dataset: Path, tmp_path: Path):
    out = tmp_path / "reduced"
    reduce_tree(dataset, out, 5, MARKER, apply=True)
    result = validate_tree(dataset, out, MARKER, divisor=5)
    assert result.ok
    assert result.summary["OK"] == 4
    assert result.summary["EMPTY_OK"] == 1


def test_validate_catches_tampered_output(dataset: Path, tmp_path: Path):
    out = tmp_path / "reduced"
    reduce_tree(dataset, out, 5, MARKER, apply=True)
    target = out / "beta" / "b1.txt"
    target.write_bytes(target.read_bytes() + make_record(999))  # sneak in an extra record
    result = validate_tree(dataset, out, MARKER, divisor=5)
    assert not result.ok
    assert result.summary["MISMATCH"] == 1


def test_validate_catches_missing_output(dataset: Path, tmp_path: Path):
    out = tmp_path / "reduced"
    reduce_tree(dataset, out, 5, MARKER, apply=True)
    (out / "alpha" / "a1.txt").unlink()
    result = validate_tree(dataset, out, MARKER, divisor=5)
    assert not result.ok
    assert result.summary["MISSING"] == 1


def test_validate_reports_extra_files(dataset: Path, tmp_path: Path):
    out = tmp_path / "reduced"
    reduce_tree(dataset, out, 5, MARKER, apply=True)
    (out / "alpha" / "stray.txt").write_bytes(make_record(1))
    result = validate_tree(dataset, out, MARKER, divisor=5)
    assert result.summary["EXTRA"] == 1
    assert result.ok  # extras are reported but are not a failure by themselves


def test_validate_divisor_one_exact_match(dataset: Path, tmp_path: Path):
    out = tmp_path / "copy"
    reduce_tree(dataset, out, 1, MARKER, apply=True)
    result = validate_tree(dataset, out, MARKER, divisor=1)
    assert result.ok
