"""Stage 3 — transform: rule-based rewriting of records.

Applies an ordered list of regex substitution rules to every record in every file.
This is the generic form of "identity isolation" from the original project: relabel
actors, mask identifiers, anonymize names — any per-record text rewrite that must not
change the *structure* of the data.

Rules live in a small JSON file so a transformation is reviewable and repeatable:

.. code-block:: json

    {
        "rules": [
            {"pattern": "\\\\bAliceP\\\\b", "replacement": "Player1"},
            {"pattern": "\\\\bBobQ\\\\b",   "replacement": "Player2"}
        ]
    }

Safety properties:

* originals are never modified — output goes to a separate root;
* after writing, every output file is re-read and its record count compared with the
  input's: a transform that accidentally creates or destroys a record boundary is
  reported as a MISMATCH instead of passing silently;
* patterns operate on raw bytes, so encodings and line endings pass through untouched.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .records import DEFAULT_GLOB, compile_marker, iter_files, split_records
from .report import write_csv

REPORT_HEADER = (
    "folder",
    "filename",
    "records",
    "records_modified",
    "replacements",
    "status",
)


@dataclass
class Rule:
    pattern: re.Pattern[bytes]
    replacement: bytes

    @classmethod
    def from_strings(cls, pattern: str, replacement: str) -> Rule:
        return cls(re.compile(pattern.encode("utf-8")), replacement.encode("utf-8"))


def load_rules(path: Path) -> list[Rule]:
    """Load substitution rules from a JSON file ({"rules": [{"pattern", "replacement"}]})."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    raw = doc.get("rules")
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{path}: expected a non-empty 'rules' list")
    rules = []
    for i, entry in enumerate(raw):
        try:
            rules.append(Rule.from_strings(entry["pattern"], entry["replacement"]))
        except (KeyError, TypeError) as exc:
            raise ValueError(f"{path}: rule #{i + 1} needs 'pattern' and 'replacement'") from exc
        except re.error as exc:
            raise ValueError(f"{path}: rule #{i + 1} has an invalid regex: {exc}") from exc
    return rules


def transform_record(record: bytes, rules: list[Rule]) -> tuple[bytes, int]:
    """Apply all rules in order to one record. Returns (new_record, replacement_count)."""
    total = 0
    for rule in rules:
        record, n = rule.pattern.subn(rule.replacement, record)
        total += n
    return record, total


@dataclass
class TransformResult:
    rows: list[tuple] = field(default_factory=list)
    records_total: int = 0
    records_modified: int = 0
    replacements: int = 0
    mismatches: int = 0

    @property
    def files(self) -> int:
        return len(self.rows)


def transform_tree(
    input_root: Path,
    output_root: Path,
    rules: list[Rule],
    marker: str,
    glob: str = DEFAULT_GLOB,
    apply: bool = False,
) -> TransformResult:
    """Transform every matching file under ``input_root`` into ``output_root``.

    With ``apply=False`` this is a dry run: rules are evaluated and counted but no
    file is written. With ``apply=True`` every output file is re-read and its record
    count verified against the input's.
    """
    if apply and output_root.resolve() == input_root.resolve():
        raise ValueError("output root must differ from input root (originals are never modified)")

    pattern = compile_marker(marker)
    result = TransformResult()
    for f in iter_files(input_root, glob):
        records = split_records(f.read_bytes(), pattern)
        out_records: list[bytes] = []
        modified = replacements = 0
        for record in records:
            new_record, n = transform_record(record, rules)
            out_records.append(new_record)
            modified += n > 0
            replacements += n

        status = "OK"
        if apply:
            dst = output_root / f.relative_to(input_root)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(b"".join(out_records))
            actual = len(split_records(dst.read_bytes(), pattern))  # read-back verification
            status = "OK" if actual == len(records) else "MISMATCH"

        result.mismatches += status == "MISMATCH"
        result.records_total += len(records)
        result.records_modified += modified
        result.replacements += replacements
        result.rows.append((f.parent.name, f.name, len(records), modified, replacements, status))
    return result


def write_transform_report(result: TransformResult, report_path: Path) -> None:
    write_csv(report_path, REPORT_HEADER, result.rows)
