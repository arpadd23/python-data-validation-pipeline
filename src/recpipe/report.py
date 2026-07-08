"""Small helpers for CSV audit reports.

Every pipeline stage can emit a per-file CSV report so a run is auditable after the
fact. Reports are plain CSV with a header row — easy to open in a spreadsheet or diff
between runs.
"""
from __future__ import annotations

import csv
from collections.abc import Iterable, Sequence
from pathlib import Path


def write_csv(path: Path, header: Sequence[str], rows: Iterable[Sequence[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)
