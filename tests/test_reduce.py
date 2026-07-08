from __future__ import annotations

from pathlib import Path

import pytest
from conftest import MARKER, make_record

from recpipe.records import compile_marker, split_records
from recpipe.reduce import even_indices, keep_count, reduce_data, reduce_tree


class TestKeepCount:
    def test_zero_records(self):
        assert keep_count(0, 5) == 0

    def test_floor_of_one_for_any_divisor(self):
        assert keep_count(1, 1000) == 1
        assert keep_count(3, 1000) == 1

    def test_half_up_rounding(self):
        assert keep_count(10, 4) == 3   # 2.5 rounds up
        assert keep_count(9, 4) == 2    # 2.25 rounds down

    def test_divisor_one_keeps_all(self):
        assert keep_count(17, 1) == 17

    def test_invalid_divisor(self):
        with pytest.raises(ValueError):
            keep_count(10, 0)


class TestEvenIndices:
    def test_keep_all(self):
        assert even_indices(5, 5) == [0, 1, 2, 3, 4]
        assert even_indices(5, 9) == [0, 1, 2, 3, 4]

    def test_spread_across_whole_range(self):
        idx = even_indices(100, 4)
        assert len(idx) == 4
        assert idx[0] < 25 and idx[-1] >= 75  # not just the head of the file
        assert idx == sorted(set(idx))

    def test_indices_in_bounds(self):
        for n in (1, 2, 7, 100, 1234):
            for keep in (1, 2, 3, n):
                idx = even_indices(n, keep)
                assert all(0 <= i < n for i in idx)
                assert len(idx) == len(set(idx))


def test_reduce_data_counts():
    data = b"".join(make_record(i) for i in range(20))
    pattern = compile_marker(MARKER)
    out, original, kept = reduce_data(data, 5, pattern)
    assert original == 20
    assert kept == 4
    assert len(split_records(out, pattern)) == 4


def test_reduce_data_records_are_verbatim_subset():
    records = [make_record(i) for i in range(12)]
    pattern = compile_marker(MARKER)
    out, _, _ = reduce_data(b"".join(records), 3, pattern)
    normalized = {r.rstrip(b"\r\n") for r in records}
    for record in split_records(out, pattern):
        assert record.rstrip(b"\r\n") in normalized


def test_reduce_tree_dry_run_writes_nothing(dataset: Path, tmp_path: Path):
    out = tmp_path / "reduced"
    result = reduce_tree(dataset, out, 5, MARKER, apply=False)
    assert not out.exists()
    assert result.records_before == 39
    assert result.mismatches == 0


def test_reduce_tree_apply_and_readback(dataset: Path, tmp_path: Path):
    out = tmp_path / "reduced"
    result = reduce_tree(dataset, out, 5, MARKER, apply=True)
    assert result.mismatches == 0
    # 10/5=2, 3/5 -> floor 1, 1/5 -> floor 1, 25/5=5, 0 -> 0
    assert result.records_after == 2 + 1 + 1 + 5 + 0
    assert (out / "alpha" / "a1.txt").exists()
    assert (out / "beta" / "b2.txt").read_bytes() == b""  # empty in, no records out


def test_reduce_tree_never_empties_nonempty_file(dataset: Path, tmp_path: Path):
    result = reduce_tree(dataset, tmp_path / "r", 10_000, MARKER, apply=True)
    for row in result.rows:
        original, actual = row[2], row[5]
        if original > 0:
            assert actual >= 1


def test_reduce_tree_refuses_output_equal_input(dataset: Path):
    with pytest.raises(ValueError):
        reduce_tree(dataset, dataset, 5, MARKER, apply=True)


def test_reduce_tree_originals_untouched(dataset: Path, tmp_path: Path):
    before = {f: f.read_bytes() for f in dataset.rglob("*.txt")}
    reduce_tree(dataset, tmp_path / "r", 3, MARKER, apply=True)
    after = {f: f.read_bytes() for f in dataset.rglob("*.txt")}
    assert before == after
