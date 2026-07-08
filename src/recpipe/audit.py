"""Stage 1 — audit: understand a dataset before touching it.

Walks a tree of record-based text files and reports, per file: record count, byte
size and a content hash. From the hashes it detects two classes of data-quality
problems that are easy to miss at scale:

* **duplicate files** — identical content under different names/paths, which silently
  double-counts records in any downstream aggregate;
* **duplicate folders** — folders whose entire file content is identical to another
  folder's (e.g. a ``dataset_old`` / ``dataset_fixed`` pair that both survived).

The audit never writes into the dataset; it only reads and reports.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from .records import DEFAULT_GLOB, compile_marker, count_records, iter_files
from .report import write_csv

REPORT_HEADER = ("folder", "filename", "records", "bytes", "sha256", "flags")


@dataclass
class FileAudit:
    path: Path
    relpath: Path
    records: int
    size: int
    sha256: str

    @property
    def flags(self) -> str:
        return "EMPTY" if self.records == 0 else ""


@dataclass
class AuditResult:
    root: Path
    files: list[FileAudit] = field(default_factory=list)
    duplicate_file_groups: list[list[Path]] = field(default_factory=list)
    duplicate_folder_groups: list[list[Path]] = field(default_factory=list)

    @property
    def total_records(self) -> int:
        return sum(f.records for f in self.files)

    @property
    def total_bytes(self) -> int:
        return sum(f.size for f in self.files)

    @property
    def empty_files(self) -> list[FileAudit]:
        return [f for f in self.files if f.records == 0]

    @property
    def has_findings(self) -> bool:
        return bool(self.duplicate_file_groups or self.duplicate_folder_groups or self.empty_files)


def audit_tree(root: Path, marker: str, glob: str = DEFAULT_GLOB) -> AuditResult:
    """Audit every matching file under ``root``. Read-only."""
    pattern = compile_marker(marker)
    result = AuditResult(root=root)

    by_hash: dict[str, list[Path]] = {}
    for f in iter_files(root, glob):
        data = f.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        result.files.append(
            FileAudit(
                path=f,
                relpath=f.relative_to(root),
                records=count_records(data, pattern),
                size=len(data),
                sha256=digest,
            )
        )
        by_hash.setdefault(digest, []).append(f)

    result.duplicate_file_groups = [paths for paths in by_hash.values() if len(paths) > 1]

    # A folder's fingerprint is the multiset of its files' content hashes; two folders
    # with the same non-empty fingerprint hold identical data under different names.
    by_folder: dict[Path, list[str]] = {}
    for fa in result.files:
        by_folder.setdefault(fa.path.parent, []).append(fa.sha256)
    fingerprints: dict[tuple[str, ...], list[Path]] = {}
    for folder, hashes in by_folder.items():
        fingerprints.setdefault(tuple(sorted(hashes)), []).append(folder)
    result.duplicate_folder_groups = [
        sorted(folders) for fp, folders in fingerprints.items() if len(folders) > 1 and fp
    ]

    return result


def write_audit_report(result: AuditResult, report_path: Path) -> None:
    rows = [
        (f.relpath.parent.as_posix(), f.path.name, f.records, f.size, f.sha256, f.flags)
        for f in result.files
    ]
    write_csv(report_path, REPORT_HEADER, rows)
