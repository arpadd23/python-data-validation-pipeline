# Large-Scale Text Data Processing & Validation Pipeline

**A Python automation project for reducing, transforming and validating millions of
semi-structured text records — built for a real client, audited end to end.**

> 📄 Full write-up: **[docs/CASE_STUDY_EN.md](docs/CASE_STUDY_EN.md)**

---

## 1. Executive summary

A client held **millions of semi-structured text records** across tens of thousands of
files — too large, too noisy, and too unreliable to analyze efficiently in their analytics
software. I built an **automated Python pipeline** that audited, reduced (~17×), transformed
and validated the data into a clean, **import-ready ~1.13M-record dataset** — with **zero
validation mismatches** and without ever modifying the original files. Along the way I
diagnosed and **worked around a silent deduplication issue in the third-party software**
that had been distorting the client's import results.

This is a **data-automation / data-engineering** project. The domain happened to be poker
hand histories, but the work is parsing, sampling, transformation, validation and audit at
scale.

---

## 2. Problem

The raw archive was organized into 37 dataset folders across three categories; each file
held a variable number of records (40–2,000+). In this state the data was:

- **too large** to import and analyze quickly,
- **noisy** — irrelevant entries polluted the metrics the client cared about,
- **fragile** — one malformed byte and the analytics tool silently drops the record,
- **partly duplicated** — some datasets existed twice under different names.

The client needed it **shrunk, cleaned, restructured and made import-ready** — without
distorting the statistical picture.

---

## 3. Solution pipeline (4 stages)

| Stage | What it does |
|-------|--------------|
| **1–2 · Audit & Reduce** | File-level audit + reports, then **target-driven proportional sampling** (evenly sampled within each file, weighted per category) so the smaller sample preserves the original distribution. |
| **3 · Identity isolation** | Section-aware text rewriting to relabel "noise" actors so they don't pollute the real analysis targets' statistics. |
| **4 · Perspective duplication** | Each record regenerated from two analytical viewpoints with **unique IDs and timestamps**, so the analytics tool's content-deduplication can't collapse them. |

```
 RAW INPUT            AUDIT + REDUCE        IDENTITY          PERSPECTIVE        IMPORT-READY
 ~64.9k files  ──►  proportional   ──►   isolation   ──►   duplication  ──►   ~1.13M records
 ~11.6M recs        sampling             (relabel)         (2 views,          (0 mismatches)
 37 folders            │                                    unique id+time)
      └─ dedup ──►  ~9.7M recs ──►  ~567k representative records
        [ every stage: re-read & validated · originals never overwritten ]
```

---

## 4. Results & business value

| Metric | Value |
|--------|-------|
| Raw input | ~64,900 files · ~11.6M records · 37 folders |
| After data-quality dedup (3 duplicate folders removed) | ~59,700 files · ~9.7M records · 34 folders |
| Reduced representative sample | **~567,000 records** (5–46× per category) |
| Final import-ready dataset | **~1.13M records** |
| Validation mismatches | **0** |
| Original data overwritten | **Never** |

- Replaced **manual, error-prone handling** with a repeatable, parameterized pipeline.
- **~17× smaller** dataset, distribution preserved → faster, lighter, more reliable imports.
- **Audited, validated output** the client can trust.
- **Surfaced and fixed hidden data-quality issues** (duplicate datasets) the client hadn't noticed.
- **Diagnosed and worked around a silent third-party deduplication issue** that had been
  distorting the client's import results.
- **Reusable scripts + documentation** delivered.

---

## 5. Technical challenges (the diagnostic moments)

- **Rejected a misleading "obvious" approach.** The intuitive "divide by the smallest file"
  rule would have produced near-zero reduction; I proved a built-in floor guaranteed no
  record loss at *any* divisor, so the divisor could be chosen by *goal* instead.
- **Solved a "numbers don't match" mystery.** Proved my output was bit-for-bit correct via
  hash-level analysis, then traced the fault to the analytics tool's **ID-based dedup** plus
  import accumulation — resolved with a clean-database protocol.
- **Caught a hidden data-quality bug** — duplicate `_old`/`_fixed` folders with identical
  counts (double-counting risk), excluded.
- **Defeated content-based deduplication** with unique, incrementing timestamps; proved the
  remaining ~3% was genuine duplicate content (zero information loss).

---

## 6. Tools

Python (`re`, `pathlib`, `openpyxl`), CSV/Excel reporting, **binary-safe file I/O**
(CRLF & encoding preserved), Windows/PowerShell, Hand2Note (client analytics tool).

---

## 7. Validation approach

Reliability was a first-class goal, not an afterthought:

- **Dry-run → apply** pattern on every transformation (preview counts before writing).
- **Read-back verification:** every output file is re-parsed and its record count compared
  to the expected count → status `OK` / `MISMATCH` (final result: **0 mismatches**).
- **Independent verification script** (`src/verify_report.py`) that re-derives the numbers
  from scratch — a separate code path, so a reducer bug can't hide in its own self-check.
- **Per-file audit reports** — see [`samples/audit_report_sample.csv`](samples/audit_report_sample.csv).
- **Defensive output:** originals are never overwritten; every stage writes to a new root.

---

## 8. Repository structure

```
.
├── README.md
├── docs/
│   └── CASE_STUDY_EN.md          # full case study
├── src/
│   ├── reduce_proportional.py    # stage 1–2: audit + proportional reduction (+ CSV report)
│   └── verify_report.py          # independent validation pass
└── samples/                      # synthetic, NO client data
    ├── sample_input.txt          # one raw record (standard format)
    ├── sample_output.txt         # the same record after stages 3–4 (illustrative)
    └── audit_report_sample.csv   # per-file validation report shape
```

Try it on the synthetic sample:

```bash
python src/reduce_proportional.py --input samples --output out --divisor 5 --apply
python src/verify_report.py     --input samples --output out --divisor 5
```

---

## Disclaimer

- **No client data is included in this repository.** The original hand-history files,
  client datasets, and any tool-specific import files are **not shared**.
- The files under [`samples/`](samples/) are **synthetic, fabricated examples** — they
  contain no real or client data.
- Numbers describe the scale and outcome of the work; the underlying data remains private
  to the client.

---

## License

Released under the **[MIT License](LICENSE)** — free to reuse with attribution.

---

*Full case study: **[docs/CASE_STUDY_EN.md](docs/CASE_STUDY_EN.md)**.*
