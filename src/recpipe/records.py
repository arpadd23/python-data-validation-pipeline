"""Core primitives for record-based text files.

A "record-based text file" is a plain-text file containing many records back to back,
where each record begins at a line starting with a known marker string (for example
``"PokerStars Hand #"`` in poker hand histories, or ``"BEGIN:VCARD"`` in vCard exports).

Everything here operates on raw bytes on purpose: the pipeline must never re-encode,
re-wrap or normalize the data it passes through. CRLF line endings, encodings and any
malformed bytes are preserved exactly as found.
"""
from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

DEFAULT_GLOB = "*.txt"


def compile_marker(marker: str) -> re.Pattern[bytes]:
    """Compile a record-start marker into a byte-level, start-of-line regex."""
    if not marker:
        raise ValueError("marker must be a non-empty string")
    return re.compile(rb"(?m)^" + re.escape(marker.encode("utf-8")))


def split_records(data: bytes, marker: re.Pattern[bytes]) -> list[bytes]:
    """Split file content into records (marker .. next marker), preserving raw bytes.

    Any preamble before the first marker is not part of a record and is dropped;
    a file with no marker at all yields no records.
    """
    starts = [m.start() for m in marker.finditer(data)]
    if not starts:
        return []
    starts.append(len(data))
    return [data[starts[i] : starts[i + 1]] for i in range(len(starts) - 1)]


def count_records(data: bytes, marker: re.Pattern[bytes]) -> int:
    """Count records without materializing them."""
    return sum(1 for _ in marker.finditer(data))


def iter_files(root: Path, glob: str = DEFAULT_GLOB) -> Iterator[Path]:
    """Yield matching files under ``root`` recursively, in stable sorted order."""
    yield from sorted(p for p in root.rglob(glob) if p.is_file())
