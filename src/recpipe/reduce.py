"""Stage 2 — reduce: proportional, distribution-preserving down-sampling.

For every file we keep an evenly-spaced subset of its records, so the reduced dataset
preserves the original per-file distribution. Two properties make this safe to use
with an arbitrary reduction factor:

* **half-up rounding** keeps the aggregate reduction close to ``1/divisor``;
* **a floor of one record per non-empty file** guarantees no file is ever emptied,
  for *any* divisor — so the divisor can be chosen by target size rather than being
  constrained by the smallest file in the dataset.

Originals are never modified: output goes to a separate root, every written file is
re-read and re-counted (read-back verification), and a per-file audit report records
expected vs. actual counts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .records import DEFAULT_GLOB, compile_marker, iter_files, split_records
from .report import write_csv

REPORT_HEADER = (
    "folder",
    "filename",
    "original_count",
    "divisor",
    "expected_keep_count",
    "actual_after_count",
    "status",
)


def keep_count(n: int, divisor: int) -> int:
    """How many of ``n`` records to keep: half-up rounding, floor of 1 if non-empty."""
    if divisor < 1:
        raise ValueError("divisor must be >= 1")
    if n == 0:
        return 0
    return max(1, int(n / divisor + 0.5))


def even_indices(n: int, keep: int) -> list[int]:
    """``keep`` evenly spaced indices across [0, n) — sample the whole file, not the head."""
    if keep >= n:
        return list(range(n))
    return [int((i + 0.5) * n / keep) for i in range(keep)]


def reduce_data(data: bytes, divisor: int, marker_pattern) -> tuple[bytes, int, int]:
    """Reduce one file's content. Returns (new_bytes, original_count, kept_count)."""
    records = split_records(data, marker_pattern)
    n = len(records)
    keep = keep_count(n, divisor)
    if keep == 0:
        return b"", n, 0
    chosen = [records[i] for i in even_indices(n, keep)]
    out = b"".join(chosen).rstrip(b"\r\n") + b"\r\n"  # keep CRLF endings intact
    return out, n, len(chosen)


@dataclass
class ReduceResult:
    rows: list[tuple] = field(default_factory=list)
    records_before: int = 0
    records_after: int = 0
    mismatches: int = 0

    @property
    def files(self) -> int:
        return len(self.rows)

    @property
    def ratio(self) -> float | None:
        return self.records_before / self.records_after if self.records_after else None


def reduce_tree(
    input_root: Path,
    output_root: Path,
    divisor: int,
    marker: str,
    glob: str = DEFAULT_GLOB,
    apply: bool = False,
) -> ReduceResult:
    """Reduce every matching file under ``input_root`` into ``output_root``.

    With ``apply=False`` this is a dry run: everything is computed and reported, but
    no file is written. With ``apply=True`` each output file is written and then
    immediately re-read and re-counted, so the report reflects what is actually on
    disk, not what the reducer believes it wrote.
    """
    if apply and output_root.resolve() == input_root.resolve():
        raise ValueError("output root must differ from input root (originals are never modified)")

    pattern = compile_marker(marker)
    result = ReduceResult()
    for f in iter_files(input_root, glob):
        data = f.read_bytes()
        new_data, original, kept = reduce_data(data, divisor, pattern)
        actual = kept
        if apply:
            dst = output_root / f.relative_to(input_root)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(new_data)
            actual = len(split_records(dst.read_bytes(), pattern))  # read-back verification
        expected = keep_count(original, divisor)
        if original == 0:
            status = "EMPTY_OK" if actual == 0 else "MISMATCH"
        else:
            status = "OK" if actual == expected else "MISMATCH"
        result.mismatches += status == "MISMATCH"
        result.records_before += original
        result.records_after += actual
        result.rows.append(
            (f.parent.name, f.name, original, divisor, expected, actual, status)
        )
    return result


def write_reduce_report(result: ReduceResult, report_path: Path) -> None:
    write_csv(report_path, REPORT_HEADER, result.rows)
