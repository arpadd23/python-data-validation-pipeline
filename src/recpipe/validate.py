"""Stage 4 — validate: independent verification of a pipeline run.

Re-reads the input and output trees from scratch and recomputes, per file, the
expected and actual record counts. This is deliberately a *separate code path* from
the reduce/transform stages: a bug in a stage cannot hide inside its own self-check.

Expectations:

* after a **reduce** run, pass the same ``divisor`` — each output file must hold
  ``keep_count(original, divisor)`` records;
* after a **transform** run (or a plain copy), use ``divisor=1`` — counts must match
  exactly.

Statuses per file: ``OK``, ``MISMATCH``, ``EMPTY_OK`` (empty in, empty out),
``MISSING`` (no output file). Files present only in the output tree are reported as
``EXTRA``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .records import DEFAULT_GLOB, compile_marker, iter_files, split_records
from .reduce import keep_count
from .report import write_csv

REPORT_HEADER = (
    "folder",
    "filename",
    "original_count",
    "expected_count",
    "actual_count",
    "status",
)


@dataclass
class ValidateResult:
    rows: list[tuple] = field(default_factory=list)
    summary: dict = field(default_factory=lambda: {
        "OK": 0, "MISMATCH": 0, "EMPTY_OK": 0, "MISSING": 0, "EXTRA": 0,
    })

    @property
    def ok(self) -> bool:
        return self.summary["MISMATCH"] == 0 and self.summary["MISSING"] == 0

    @property
    def files(self) -> int:
        return len(self.rows)


def validate_tree(
    input_root: Path,
    output_root: Path,
    marker: str,
    divisor: int = 1,
    glob: str = DEFAULT_GLOB,
) -> ValidateResult:
    """Validate ``output_root`` against ``input_root``. Read-only."""
    pattern = compile_marker(marker)
    result = ValidateResult()

    input_files = list(iter_files(input_root, glob))
    expected_outputs = {output_root / f.relative_to(input_root) for f in input_files}

    for f in input_files:
        original = len(split_records(f.read_bytes(), pattern))
        expected = keep_count(original, divisor)
        dst = output_root / f.relative_to(input_root)
        if not dst.exists():
            status, actual = "MISSING", 0
        else:
            actual = len(split_records(dst.read_bytes(), pattern))
            if original == 0:
                status = "EMPTY_OK" if actual == 0 else "MISMATCH"
            else:
                status = "OK" if actual == expected else "MISMATCH"
        result.summary[status] += 1
        result.rows.append((f.parent.name, f.name, original, expected, actual, status))

    if output_root.exists():
        for f in iter_files(output_root, glob):
            if f not in expected_outputs:
                result.summary["EXTRA"] += 1
                actual = len(split_records(f.read_bytes(), pattern))
                result.rows.append((f.parent.name, f.name, "", "", actual, "EXTRA"))

    return result


def write_validate_report(result: ValidateResult, report_path: Path) -> None:
    write_csv(report_path, REPORT_HEADER, result.rows)
