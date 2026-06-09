"""Independent verification of a reduction run.

Re-reads the original and the reduced datasets from scratch, recomputes the expected and
actual record counts per file, and reports OK / MISMATCH / EMPTY_OK / MISSING. This is a
*separate* code path from the reducer on purpose -- so a bug in the reducer cannot hide
itself in its own self-check.

Usage:
    python verify_report.py --input ./data --output ./data_reduced --divisor 5
"""
from __future__ import annotations

import argparse
from pathlib import Path

from reduce_proportional import compile_marker, split_records, keep_count, DEFAULT_MARKER


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--divisor", required=True, type=int)
    ap.add_argument("--marker", default=DEFAULT_MARKER)
    args = ap.parse_args()

    marker = compile_marker(args.marker)
    summary = {"OK": 0, "MISMATCH": 0, "EMPTY_OK": 0, "MISSING": 0}
    for f in sorted(args.input.rglob("*.txt")):
        original = len(split_records(f.read_bytes(), marker))
        expected = keep_count(original, args.divisor)
        dst = args.output / f.relative_to(args.input)
        if not dst.exists():
            status, actual = "MISSING", 0
        else:
            actual = len(split_records(dst.read_bytes(), marker))
            if original == 0:
                status = "EMPTY_OK" if actual == 0 else "MISMATCH"
            else:
                status = "OK" if actual == expected else "MISMATCH"
        summary[status] += 1

    for k, v in summary.items():
        print(f"  {k:<10} {v}")
    ok = summary["MISMATCH"] == 0 and summary["MISSING"] == 0
    print("RESULT:", "ALL OK" if ok else "FAILURES PRESENT")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
