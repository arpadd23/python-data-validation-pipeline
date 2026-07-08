# Examples

Everything in this directory is **synthetic**. The sample dataset is generated from a
fixed random seed by [generate_sample_data.py](generate_sample_data.py) — no real or
client data appears anywhere in this repository.

## Contents

| Path | What it is |
|---|---|
| `sample_data/` | 13 files / 240 records in the public PokerStars hand-history text format, used by the README quickstart and the CI smoke job. |
| `rules/anonymize.json` | Demo transform rules: anonymize the six fictional player names. |
| `generate_sample_data.py` | Regenerates `sample_data/` from scratch (`python examples/generate_sample_data.py`). |

## Planted data-quality problems

The dataset intentionally contains the two problems `recpipe audit` exists to catch,
mirroring what actually happened in the original project:

- **`TableTypeA_old/`** is a byte-for-byte duplicate of **`TableTypeA/`** — the classic
  "an old copy survived under another name" hazard that double-counts records.
- **`TableTypeB/session_04.txt`** is empty.

Run the quickstart from the repository root:

```bash
recpipe audit --input examples/sample_data --marker "PokerStars Hand #"
```

and both problems are reported. See the [README](../README.md#quickstart) for the full
audit → reduce → transform → validate walkthrough.

## Why poker hands?

The original project (see [the case study](../docs/CASE_STUDY_EN.md)) processed poker
simulator output, so the sample data uses the same public text format. recpipe itself
is format-agnostic: point `--marker` at whatever your records start with.
