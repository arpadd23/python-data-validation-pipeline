from __future__ import annotations

import shutil
from pathlib import Path

from conftest import MARKER

from recpipe.audit import audit_tree, write_audit_report


def test_audit_counts(dataset: Path):
    result = audit_tree(dataset, MARKER)
    assert len(result.files) == 5
    assert result.total_records == 39
    assert [f.path.name for f in result.empty_files] == ["b2.txt"]


def test_audit_is_read_only(dataset: Path):
    before = {f: f.read_bytes() for f in dataset.rglob("*.txt")}
    audit_tree(dataset, MARKER)
    assert {f: f.read_bytes() for f in dataset.rglob("*.txt")} == before


def test_audit_detects_duplicate_files(dataset: Path):
    dup = dataset / "alpha" / "a1_copy.txt"
    shutil.copyfile(dataset / "alpha" / "a1.txt", dup)
    result = audit_tree(dataset, MARKER)
    assert len(result.duplicate_file_groups) == 1
    names = {p.name for p in result.duplicate_file_groups[0]}
    assert names == {"a1.txt", "a1_copy.txt"}


def test_audit_detects_duplicate_folders(dataset: Path):
    shutil.copytree(dataset / "alpha", dataset / "alpha_old")
    result = audit_tree(dataset, MARKER)
    assert len(result.duplicate_folder_groups) == 1
    names = {p.name for p in result.duplicate_folder_groups[0]}
    assert names == {"alpha", "alpha_old"}


def test_audit_clean_dataset_has_no_folder_findings(dataset: Path):
    result = audit_tree(dataset, MARKER)
    assert result.duplicate_file_groups == []
    assert result.duplicate_folder_groups == []


def test_audit_report_written(dataset: Path, tmp_path: Path):
    result = audit_tree(dataset, MARKER)
    report = tmp_path / "audit.csv"
    write_audit_report(result, report)
    lines = report.read_text(encoding="utf-8").strip().splitlines()
    assert lines[0].startswith("folder,filename,records")
    assert len(lines) == 1 + 5
