# Contributing to recpipe

Thanks for your interest! recpipe is an early-stage project — contributions of every
size are welcome, from typo fixes to roadmap features.

## Getting set up

```bash
git clone https://github.com/arpadd23/python-data-validation-pipeline.git
cd python-data-validation-pipeline
pip install -e ".[dev]"
```

Run the checks the CI runs:

```bash
ruff check src tests examples
pytest
```

Both must pass before a PR can merge. There are no other gates.

## Finding something to work on

- Check the [good first issues in the roadmap](docs/ROADMAP.md#good-first-issues).
- Browse open issues — anything unassigned is up for grabs; leave a comment so work
  isn't duplicated.
- For anything larger than a small fix, **open an issue before writing code** so we
  can agree on the approach.

## Project principles (please keep these intact)

1. **Originals are never modified.** Any code path that writes must target a separate
   output root and refuse `output == input`.
2. **Dry run by default.** Commands that write take `--apply`; without it they must
   not touch the filesystem.
3. **Verify what was written.** Written files are re-read and re-counted; `validate`
   stays an independent code path from the writing stages.
4. **Bytes in, bytes out.** The pipeline must not re-encode or normalize data.
   Preserve CRLF, encodings, malformed bytes.
5. **Stdlib only** in the core package. Dev tooling (pytest, ruff) is fine.

## Pull requests

- Keep PRs focused — one change per PR.
- Add or update tests for any behavior change; `tests/` mirrors the module layout.
- Update the README/docs if you change CLI flags or output.
- Note user-visible changes in `CHANGELOG.md` under "Unreleased".

## Reporting bugs

Use the bug report issue template. The most useful thing you can include is a tiny
reproduction: a few small synthetic files (never real data!) plus the exact command
and output.

## Code of conduct

Be kind and constructive. Assume good faith. Disagreements about code are fine;
personal attacks are not.
