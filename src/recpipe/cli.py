"""Command-line interface: ``recpipe audit | reduce | transform | validate``.

Design rules shared by all commands:

* ``--marker`` is always explicit — recpipe never guesses where a record starts;
* commands that write output take ``--apply``; without it they are a dry run;
* every command can write a per-file CSV report with ``--report``;
* exit code 0 means clean, 1 means mismatches/failures were found, 2 means bad usage.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .audit import audit_tree, write_audit_report
from .records import DEFAULT_GLOB
from .reduce import reduce_tree, write_reduce_report
from .transform import load_rules, transform_tree, write_transform_report
from .validate import validate_tree, write_validate_report


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--marker", required=True,
                        help="String a record-start line begins with (e.g. 'PokerStars Hand #').")
    parser.add_argument("--glob", default=DEFAULT_GLOB,
                        help=f"Filename pattern to match (default: {DEFAULT_GLOB}).")
    parser.add_argument("--report", type=Path, default=None,
                        help="Write a per-file CSV report to this path.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="recpipe",
        description="Audit, reduce, transform and validate large record-based text datasets.",
    )
    parser.add_argument("--version", action="version", version=f"recpipe {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("audit", help="Read-only survey: counts, sizes, duplicates, empty files.")
    p.add_argument("--input", required=True, type=Path, help="Dataset root (scanned recursively).")
    _add_common(p)
    p.add_argument("--strict", action="store_true",
                   help="Exit 1 if duplicates or empty files are found.")

    p = sub.add_parser("reduce", help="Proportional, distribution-preserving down-sampling.")
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path,
                   help="Output root (must differ from input; originals are never modified).")
    p.add_argument("--divisor", required=True, type=int,
                   help="Reduction factor; every non-empty file keeps at least 1 record.")
    _add_common(p)
    p.add_argument("--apply", action="store_true", help="Write files (otherwise dry run).")

    p = sub.add_parser("transform", help="Apply regex substitution rules to every record.")
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--rules", required=True, type=Path,
                   help="JSON rules file: {\"rules\": [{\"pattern\", \"replacement\"}, ...]}.")
    _add_common(p)
    p.add_argument("--apply", action="store_true", help="Write files (otherwise dry run).")

    p = sub.add_parser("validate", help="Independently verify an output tree against its input.")
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--divisor", type=int, default=1,
                   help="Divisor used by the reduce run being checked (default 1: exact match).")
    _add_common(p)

    return parser


def _cmd_audit(args: argparse.Namespace) -> int:
    result = audit_tree(args.input, args.marker, args.glob)
    print(f"files={len(result.files)}  records={result.total_records:,}  "
          f"bytes={result.total_bytes:,}")
    if result.empty_files:
        print(f"empty files: {len(result.empty_files)}")
    for group in result.duplicate_file_groups:
        rel = ", ".join(str(p.relative_to(args.input)) for p in group)
        print(f"DUPLICATE FILES ({len(group)}): {rel}")
    for group in result.duplicate_folder_groups:
        rel = ", ".join(str(p.relative_to(args.input)) for p in group)
        print(f"DUPLICATE FOLDERS ({len(group)}): {rel}")
    if args.report:
        write_audit_report(result, args.report)
        print(f"report: {args.report}")
    return 1 if (args.strict and result.has_findings) else 0


def _cmd_reduce(args: argparse.Namespace) -> int:
    result = reduce_tree(args.input, args.output, args.divisor, args.marker,
                         args.glob, apply=args.apply)
    ratio = f"{result.ratio:.1f}x" if result.ratio else "-"
    print(f"files={result.files}  records: {result.records_before:,} -> "
          f"{result.records_after:,} ({ratio})  mismatches={result.mismatches}")
    if args.report:
        write_reduce_report(result, args.report)
        print(f"report: {args.report}")
    if not args.apply:
        print("(dry run — no files written; pass --apply to write)")
    return 1 if result.mismatches else 0


def _cmd_transform(args: argparse.Namespace) -> int:
    rules = load_rules(args.rules)
    result = transform_tree(args.input, args.output, rules, args.marker,
                            args.glob, apply=args.apply)
    print(f"files={result.files}  records={result.records_total:,}  "
          f"modified={result.records_modified:,}  replacements={result.replacements:,}  "
          f"mismatches={result.mismatches}")
    if args.report:
        write_transform_report(result, args.report)
        print(f"report: {args.report}")
    if not args.apply:
        print("(dry run — no files written; pass --apply to write)")
    return 1 if result.mismatches else 0


def _cmd_validate(args: argparse.Namespace) -> int:
    result = validate_tree(args.input, args.output, args.marker,
                           divisor=args.divisor, glob=args.glob)
    for status, count in result.summary.items():
        if count:
            print(f"  {status:<10} {count}")
    print("RESULT:", "ALL OK" if result.ok else "FAILURES PRESENT")
    if args.report:
        write_validate_report(result, args.report)
        print(f"report: {args.report}")
    return 0 if result.ok else 1


_COMMANDS = {
    "audit": _cmd_audit,
    "reduce": _cmd_reduce,
    "transform": _cmd_transform,
    "validate": _cmd_validate,
}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return _COMMANDS[args.command](args)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
