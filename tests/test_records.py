from __future__ import annotations

import pytest

from recpipe.records import compile_marker, count_records, split_records

MARKER = compile_marker("### RECORD ")


def test_split_empty_data():
    assert split_records(b"", MARKER) == []


def test_split_no_marker():
    assert split_records(b"just some text\r\nwith lines\r\n", MARKER) == []


def test_split_preserves_bytes_exactly():
    data = b"### RECORD 1\r\nline\r\n### RECORD 2\r\nother\xff\xfebytes\r\n"
    records = split_records(data, MARKER)
    assert len(records) == 2
    assert b"".join(records) == data  # nothing lost, nothing re-encoded


def test_split_drops_preamble_before_first_marker():
    data = b"junk header\r\n### RECORD 1\r\nbody\r\n"
    records = split_records(data, MARKER)
    assert len(records) == 1
    assert records[0].startswith(b"### RECORD 1")


def test_marker_must_match_line_start():
    data = b"prefix ### RECORD 1\r\nbody\r\n"
    assert split_records(data, MARKER) == []


def test_count_matches_split():
    data = b"### RECORD 1\r\na\r\n### RECORD 2\r\nb\r\n### RECORD 3\r\nc\r\n"
    assert count_records(data, MARKER) == len(split_records(data, MARKER)) == 3


def test_empty_marker_rejected():
    with pytest.raises(ValueError):
        compile_marker("")


def test_marker_with_regex_specials_is_escaped():
    pattern = compile_marker("Hand #(1)*")
    assert count_records(b"Hand #(1)*\r\nbody\r\n", pattern) == 1
