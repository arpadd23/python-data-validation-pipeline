"""Proportional, distribution-preserving down-sampling of record-based text files.

Each input file holds many records separated by a fixed line marker. For every file we
keep a proportional, evenly-spaced subset of its records, so the reduced dataset preserves
the original per-file distribution -- while guaranteeing at least one record per non-empty
file. Originals are never modified; output goes to a separate root, and a per-file audit
report (CSV) is written.

This is a cleaned, generic version of a script built for a real client project; it carries
no client data or paths.

Usage:
    python reduce_proportional.py --input ./data --output ./data_reduced --divisor 5
    python reduce_proportional.py --input ./data --output ./data_reduced --divisor 5 --apply

Without --apply it is a dry run (counts + report only, no files written).
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

# A record begins at a line starting with this marker (override with --marker).
DEFAULT_MARKER = "PokerStars Hand #"


def compile_marker(marker: str) -> re.Pattern[bytes]:
    return re.compile(rb"(?m)^" + re.escape(marker.encode()))


def split_records(data: bytes, marker: re.Pattern[bytes]) -> list[bytes]:
    """Split file bytes into records (marker .. next marker), preserving raw bytes."""
    starts = [m.start() for m in marker.finditer(data)]
    if not starts:
        return []
    starts.append(len(data))
    return [data[starts[i]:starts[i + 1]] for i in range(len(starts) - 1)]


def keep_count(n: int, divisor: int) -> int:
    """How many records to keep: half-up rounding, floor of 1 for any non-empty file.

    The floor is the key insight: it guarantees no file is ever emptied, for ANY divisor,
    so the divisor can be chosen by target density rather than by the smallest file.
    """
    if n == 0:
        return 0
    return max(1, int(n / divisor + 0.5))


def even_indices(n: int, keep: int) -> list[int]:
    """`keep` evenly spaced indices across [0, n) -- sample the whole file, not just the head."""
    if keep >= n:
        return list(range(n))
    return [int((i + 0.5) * n / keep) for i in range(keep)]


def reduce_data(data: bytes, divisor: int, marker: re.Pattern[bytes]) -> tuple[bytes, int, int]:
    """Return (new_bytes, original_count, kept_count) for one file's content."""
    records = split_records(data, marker)
    n = len(records)
    keep = keep_count(n, divisor)
    if keep == 0:
        return b"", n, 0
    chosen = [records[i] for i in even_indices(n, keep)]
    out = b"".join(chosen).rstrip(b"\r\n") + b"\r\n"  # preserve CRLF line endings
    return out, n, len(chosen)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, type=Path, help="Input root (scanned recursively).")
    ap.add_argument("--output", required=True, type=Path, help="Output root (never the input).")
    ap.add_argument("--divisor", required=True, type=int, help="Reduction factor (target-driven).")
    ap.add_argument("--marker", default=DEFAULT_MARKER, help=f"Record start marker (default: {DEFAULT_MARKER!r}).")
    ap.add_argument("--report", default="audit_report.csv", help="Per-file audit report path.")
    ap.add_argument("--apply", action="store_true", help="Write files (otherwise dry run).")
    args = ap.parse_args()

    marker = compile_marker(args.marker)
    rows, before, after, mism = [], 0, 0, 0
    for f in sorted(args.input.rglob("*.txt")):
        data = f.read_bytes()
        new_data, original, kept = reduce_data(data, args.divisor, marker)
        actual = kept
        if args.apply:
            dst = args.output / f.relative_to(args.input)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(new_data)
            actual = len(split_records(dst.read_bytes(), marker))  # read-back verification
        expected = keep_count(original, args.divisor)
        if original == 0:
            status = "EMPTY_OK" if actual == 0 else "MISMATCH"
        else:
            status = "OK" if actual == expected else "MISMATCH"
        mism += status == "MISMATCH"
        before += original
        after += actual
        rows.append((f.parent.name, f.name, original, args.divisor, expected, actual, status))

    with open(args.report, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["folder", "filename", "original_count", "divisor",
                    "expected_keep_count", "actual_after_count", "status"])
        w.writerows(rows)

    ratio = f"{before / after:.1f}x" if after else "-"
    print(f"files={len(rows)}  records: {before:,} -> {after:,} ({ratio})  mismatches={mism}")
    print(f"report: {args.report}" + ("" if args.apply else "   (DRY RUN -- no files written)"))
    return 1 if mism else 0


if __name__ == "__main__":
    raise SystemExit(main())
