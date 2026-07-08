from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import MARKER

from recpipe.transform import Rule, load_rules, transform_record, transform_tree


def rule(pattern: str, replacement: str) -> Rule:
    return Rule.from_strings(pattern, replacement)


def test_transform_record_applies_rules_in_order():
    record = b"### RECORD 1\r\nplayer: Alice\r\n"
    out, n = transform_record(record, [rule(r"\bAlice\b", "Bob"), rule(r"\bBob\b", "Carol")])
    assert b"Carol" in out and b"Alice" not in out
    assert n == 2


def test_transform_record_no_match():
    record = b"### RECORD 1\r\nplayer: Zoe\r\n"
    out, n = transform_record(record, [rule(r"\bAlice\b", "Bob")])
    assert out == record
    assert n == 0


def test_load_rules(tmp_path: Path):
    path = tmp_path / "rules.json"
    path.write_text(json.dumps({"rules": [{"pattern": "a", "replacement": "b"}]}))
    rules = load_rules(path)
    assert len(rules) == 1


@pytest.mark.parametrize("doc", [
    {},
    {"rules": []},
    {"rules": [{"pattern": "unclosed("}]},
    {"rules": [{"pattern": "(bad", "replacement": "x"}]},
])
def test_load_rules_rejects_bad_files(tmp_path: Path, doc: dict):
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(doc))
    with pytest.raises(ValueError):
        load_rules(path)


def test_transform_tree_dry_run_writes_nothing(dataset: Path, tmp_path: Path):
    out = tmp_path / "out"
    result = transform_tree(dataset, out, [rule(r"\bAlice\b", "PlayerX")], MARKER, apply=False)
    assert not out.exists()
    assert result.records_total == 39
    assert result.records_modified == 39  # every record mentions Alice
    assert result.mismatches == 0


def test_transform_tree_apply(dataset: Path, tmp_path: Path):
    out = tmp_path / "out"
    result = transform_tree(dataset, out, [rule(r"\bAlice\b", "PlayerX")], MARKER, apply=True)
    assert result.mismatches == 0
    data = (out / "alpha" / "a1.txt").read_bytes()
    assert b"PlayerX" in data and b"Alice" not in data


def test_transform_tree_detects_broken_record_boundary(dataset: Path, tmp_path: Path):
    # A rule that rewrites the marker itself changes the record count -> MISMATCH.
    result = transform_tree(
        dataset, tmp_path / "out", [rule("### RECORD", "@@@ RECORD")], MARKER, apply=True
    )
    assert result.mismatches == len(result.rows) - 1  # all except the empty file


def test_transform_tree_refuses_output_equal_input(dataset: Path):
    with pytest.raises(ValueError):
        transform_tree(dataset, dataset, [rule("a", "b")], MARKER, apply=True)
