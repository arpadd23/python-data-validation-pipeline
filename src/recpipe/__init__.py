"""recpipe — audit, reduce, transform and validate large record-based text datasets.

A small, dependency-free toolkit extracted from a real-world data validation project.
See the README for the full story and usage examples.
"""
from __future__ import annotations

from .audit import AuditResult, audit_tree, write_audit_report
from .records import compile_marker, count_records, iter_files, split_records
from .reduce import (
    ReduceResult,
    even_indices,
    keep_count,
    reduce_data,
    reduce_tree,
    write_reduce_report,
)
from .transform import (
    Rule,
    TransformResult,
    load_rules,
    transform_record,
    transform_tree,
    write_transform_report,
)
from .validate import ValidateResult, validate_tree, write_validate_report

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "compile_marker",
    "split_records",
    "count_records",
    "iter_files",
    "audit_tree",
    "write_audit_report",
    "AuditResult",
    "keep_count",
    "even_indices",
    "reduce_data",
    "reduce_tree",
    "write_reduce_report",
    "ReduceResult",
    "Rule",
    "load_rules",
    "transform_record",
    "transform_tree",
    "write_transform_report",
    "TransformResult",
    "validate_tree",
    "write_validate_report",
    "ValidateResult",
]
