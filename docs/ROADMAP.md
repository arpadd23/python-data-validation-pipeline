# Roadmap

This is a living document. Items are ordered by intent, not by promise — recpipe is an
early-stage project with a single maintainer, and the roadmap will bend to real usage
and contributor interest. If you want to work on any of these, open an issue first so
we can agree on scope.

## v0.2 — scale & ergonomics

- **Streaming record iteration.** Today every file is read fully into memory. Add a
  generator-based splitter so single multi-GB files can be reduced/transformed with
  constant memory.
- **Per-category divisor configuration.** In the original project, different dataset
  categories were reduced with different divisors to hit a global target. Support a
  small config file mapping folder patterns to divisors (`{"TableTypeA*": 10, "*": 5}`).
- **Parallel tree processing.** `--workers N` for audit/reduce/transform; files are
  independent, so this is naturally parallel.
- **`--exclude` patterns** for audit/reduce/transform (skip `_old` folders without
  moving them out).

## v0.3 — completing the original pipeline

- **Perspective duplication stage.** The last stage of the original workflow: emit
  each record K times with per-copy substitutions and unique, incrementing
  IDs/timestamps, so content-deduplicating import tools don't collapse them.
  Needs a careful generic design (template rules + counter fields).
- **JSONL report output** (`--report-format jsonl`) for piping reports into other
  tools.
- **Machine-readable summary** (`--json` on every command) for CI usage.

## Publishing

- Publish to PyPI as `recpipe` once the CLI flags have survived a couple of releases
  without breaking changes.
- Trusted-publisher GitHub Actions release workflow.

## Good first issues

Small, well-bounded tasks — each of these is a nice first contribution, and none
requires touching the core sampling logic:

1. **`--exclude` glob option** for `audit` (skip matching folders/files).
2. **`recpipe audit --json`** — print the summary as JSON to stdout.
3. **Progress output for large trees** — a simple `--verbose` flag that prints each
   file as it's processed.
4. **More sample rule files** under `examples/rules/` (e.g. masking emails or IPs in
   log-style records) with a short README section.
5. **Windows path tests** — CI runs on Windows already; add explicit tests for mixed
   path separators in `--input`/`--output`.

## Non-goals

To keep the tool small and predictable:

- No format-specific parsers (poker, logs, vCard…) in the core — recpipe only knows
  "records start at a marker line".
- No in-place modification mode. Ever.
- No heavy dependency stack; the core stays stdlib-only.
