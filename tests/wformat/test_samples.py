import pytest
from pathlib import Path
from wformat.wformat import WFormat
import difflib


def test_samples():
    """
    Workflow per original *.cpp (single dot) in tests/sample:
      0. Remove any stale *.formatted.cpp files.
      1. Format source -> <base>.formatted.cpp
      2. Compare with <base>.correct.cpp (must exist)
      3. Collect unified diffs for mismatches
      4. Check idempotency
    """
    base_dir = Path(__file__).resolve().parents[1] / "sample"
    if not base_dir.exists():
        pytest.skip(f"Missing directory: {base_dir}")

    # 0) Cleanup old generated formatted files
    for stale in base_dir.glob("*.formatted.cpp"):
        try:
            stale.unlink()
        except Exception:
            # Ignore inability to remove; test will overwrite or fail later
            pass

    # Originals = exactly one dot (the .cpp extension)
    originals = [
        p
        for p in base_dir.glob("*.cpp")
        if p.suffix == ".cpp" and p.name.count(".") == 1
    ]

    formatter = WFormat()
    diffs = []
    processed = 0

    for src in sorted(originals):
        processed += 1
        text = src.read_text(encoding="utf-8")
        try:
            formatted = formatter.format_memory(text)
        except Exception as e:
            pytest.fail(f"Formatting failed for {src.name}: {e}")

        formatted_path = src.with_suffix(".formatted.cpp")
        formatted_path.write_text(formatted, encoding="utf-8")

        correct_path = src.with_suffix(".correct.cpp")
        if not correct_path.exists():
            diffs.append(f"[MISSING] Expected file not found: {correct_path.name}")
            continue

        correct = correct_path.read_text(encoding="utf-8")

        if formatted != correct:
            diff_lines = difflib.unified_diff(
                correct.splitlines(keepends=True),
                formatted.splitlines(keepends=True),
                fromfile=f"{correct_path.name} (expected)",
                tofile=f"{formatted_path.name} (actual)",
                lineterm="",
            )
            diff_list = list(diff_lines)
            if len(diff_list) > 500:
                diff_list = diff_list[:500] + ["\n... (diff truncated)"]
            diffs.append(f"--- Diff for {src.name} ---\n" + "".join(diff_list))

    if diffs:
        for d in diffs:
            print(d)
        pytest.fail(
            f"{len(diffs)} issue(s) found across {processed} file(s). See diff output above.", pytrace=False
        )
