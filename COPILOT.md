# Copilot Task Guide

This repository is prepared for the GitHub Copilot coding agent. Follow these guardrails when making automated changes.

## Primary Objective

All tests must pass: `pytest`.

Formatting tests validate that each original C++ sample (*.cpp with exactly one dot) produces a matching `*.correct.cpp` after running wformat. Only configuration files may be changed to fix formatting differences.

## Allowed Changes

- `src/wformat/data/.clang-format`
- `src/wformat/data/uncrustify.cfg`
- New sample source files (with corresponding `.correct.cpp` after human review)
- Code improvements in Python formatter logic (if needed) but **avoid** editing baseline `*.correct.cpp` files.

## Forbidden Changes

- Do not modify existing `*.correct.cpp` baseline files to "force" tests to pass.
- Do not weaken or delete tests in `tests/wformat/`.

## Test Commands

- Full test run: `pytest -q`
- Only new samples: `pytest tests/wformat/test_new_samples.py -s`

## Formatting Pipeline

`clang-format` (coarse layout) -> `uncrustify` (fine adjustments).

Adjust `.clang-format` first (brace style, wrapping, alignment); then refine with `uncrustify.cfg` for spacing/alignment mismatches. Ensure idempotency (reformatting a formatted file yields identical output).

## Idempotency Check (manual)

```bash
wformat --stdin < tests/sample/new/foo.cpp | tee foo.formatted.cpp | wformat --stdin > foo2.cpp && diff -u foo.formatted.cpp foo2.cpp
```

## Adding a New Sample

1. Place `foo.cpp` in `tests/sample/new/` (single-dot filename).
2. Run tests to generate `foo.formatted.cpp`.
3. If output is accepted, copy or rename to `foo.correct.cpp` (human approval required).
4. Re-run tests.

## Python Environment

Install with editable mode and test extras:

```bash
pip install -e .[test]
```

## Quick Smoke Test

```bash
python - <<'PY'
from wformat.wformat import WFormat
f = WFormat(); print(f.format_memory('int  main( ){return 0;}'))
PY
```

## Definition of Done

- `pytest -q` exits 0.
- No diffs reported in formatting tests.
- No baseline or test file weakened.
- Only legitimate config / code changes.

## If Blocked

Output a brief table:

| File | Difference | Suspected Missing Option | Notes |
|------|------------|--------------------------|-------|

Then stop.

## Notes

The Copilot setup workflow (`.github/workflows/copilot-setup-steps.yml`) pre-installs Python (3.11) and Node dependencies to speed up iteration.
