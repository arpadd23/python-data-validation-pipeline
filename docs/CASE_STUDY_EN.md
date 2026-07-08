# Large-Scale Text Data Processing & Validation Pipeline

### Python automation project for reducing, transforming and validating millions of semi-structured text records.

---

## Executive Summary (the 60-second version)

A client held **millions of semi-structured text records** spread across tens of thousands
of files — too large, too noisy, and too unreliable to analyze efficiently in their
analytics software. I built an **automated Python pipeline** that:

1. **audited** the raw data and surfaced hidden quality issues (duplicate datasets),
2. **reduced** it ~17× down to a distribution-preserving representative sample,
3. **transformed** it through several stages so an external analytics tool (Hand2Note)
   could read it without distortion, and
4. **validated and audited every step** — finishing with **zero validation mismatches**,
   and never once overwriting the original data.

Along the way I diagnosed and **worked around a silent third-party deduplication
issue** that had been distorting the client's import results. The deliverable: a clean, trusted,
**import-ready ~1.13M-record dataset**, plus reusable scripts and documentation.

> *This is not a poker project. It is a data-automation project — the poker data was just
> the domain.*

---

## Problem

The client's simulator produced a huge archive of text "records," organized into 37 dataset
folders across three categories. Each file held a variable number of records (40–2,000+).

In this raw state the data was:
- **too large** to import and analyze quickly,
- **noisy** — full of irrelevant entries that polluted the metrics the client cared about,
- **fragile** — one malformed byte and the analytics tool silently drops the record,
- **partly duplicated** — some datasets existed twice under different names.

The client needed the data **shrunk, cleaned, restructured and made import-ready**, without
distorting the statistical picture.

---

## Solution — a 4-stage automated pipeline

| Stage | What it does |
|-------|--------------|
| **1–2. Audit & Reduce** | File-level audit (Excel/CSV reports), then **target-driven proportional sampling** — evenly sampled within each file, weighted per category, so the smaller sample reproduces the full data's distribution. |
| **3. Identity isolation** | Programmatic, section-aware text rewriting to relabel the "noise" actors so they no longer pollute the real analysis targets' statistics. |
| **4. Perspective duplication** | Each record regenerated from two analytical viewpoints, with **unique IDs and timestamps** so the analytics tool's content-deduplication can't collapse them. |

Every stage wrote to **separate output roots** — the original data was never modified — and
every write was **re-read and verified**.

---

## Technical Challenges (the diagnostic moments)

These are the parts that show real engineering, not just "ran a script":

- **Rejected a misleading "obvious" approach.** The intuitive rule (divide by the smallest
  file) would have produced near-zero reduction. I proved a built-in floor guaranteed no
  record loss at *any* divisor, which let me choose the divisor by *goal* instead — a
  step-change in output quality.
- **Solved a "numbers don't match" mystery.** The client's import showed inflated counts.
  Through hash-level analysis I proved my output was **bit-for-bit correct**, and traced the
  fault to the analytics tool's **ID-based deduplication** plus accumulation from earlier
  imports. Fix + protocol: a clean database before every re-import.
- **Caught a hidden data-quality bug.** I detected duplicate `_old`/`_fixed` folders with
  identical record counts (a double-counting risk) and excluded them — which is *why* the
  clean dataset is 59.7k files / 9.7M records instead of the raw 64.9k / 11.6M.
- **Defeated content-based deduplication.** When perspective-duplication lost records, I
  realized every record shared an identical timestamp, and injected unique, incrementing
  timestamps. I then proved the remaining ~3% "loss" was **genuine duplicate content**
  (zero information loss), not a defect.

---

## Results & Business Value

**By the numbers**

| Metric | Value |
|--------|-------|
| Raw input | ~64,900 files · ~11.6M records · 37 folders |
| After data-quality dedup (3 duplicate folders removed) | ~59,700 files · ~9.7M records · 34 folders |
| Reduced representative sample | **~567,000 records** (5–46× compression per category) |
| Final transformed, import-ready dataset | **~1.13M records** |
| Validation mismatches | **0** (every file re-read and verified) |
| Original data overwritten | **Never** |

**Business value**

- **Replaced manual, error-prone handling** with a repeatable, parameterized pipeline.
- **~17× smaller dataset** with the statistical distribution preserved → faster, lighter,
  more reliable imports.
- **Audited, validated output the client can trust** (0 mismatches, independent verification).
- **Surfaced and fixed hidden data-quality issues** (duplicate datasets) the client hadn't noticed.
- **Diagnosed and worked around a silent third-party deduplication issue** that had been distorting the client's import results.
- **Reusable scripts + documentation** delivered, so future runs need no rework.

---

## Pipeline at a glance

```
   RAW INPUT                AUDIT + REDUCE          IDENTITY            PERSPECTIVE         IMPORT-READY
 ~64.9k files     ─────►   proportional    ─────►  isolation   ─────►  duplication  ─────►  ~1.13M records
 ~11.6M records           sampling                (relabel noise)     (2 viewpoints,        (Hand2Note,
 37 folders                  │                                         unique id+time)       0 mismatches)
       │                     │                          ▲
       └─ data-quality ──►  ~9.7M records ──►  ~567k representative records
          dedup (34 folders)
                         [ every stage: re-read & validated · originals never overwritten ]
```

---

## Tools

Python (regex, `pathlib`, `openpyxl`), CSV/Excel reporting, binary-safe file I/O
(CRLF & encoding preserved), Windows/PowerShell, Hand2Note (client analytics tool).
Full documentation + file-based project memory for continuity.

---

## From case study to open-source toolkit

The reusable core of this work now lives in this repository as **recpipe** (see the
[README](../README.md)) — an installable package and CLI with `audit`, `reduce`,
`transform` and `validate` commands:

- Stages **1–2** (audit + proportional reduction) map to `recpipe audit` and
  `recpipe reduce`.
- Stage **3** (identity isolation) is generalized as `recpipe transform` — ordered
  regex substitution rules applied per record, with record counts verified unchanged.
- Stage **4** (perspective duplication) is not yet generalized; it is on the
  [roadmap](ROADMAP.md). An illustration of what stages 3–4 did to one record is in
  [case_study_stage34_example.txt](case_study_stage34_example.txt).
- The read-back verification and independent-validation patterns described above are
  built into every recpipe command.

All numbers in this document describe the original private engagement; the repository
itself contains only synthetic data.
