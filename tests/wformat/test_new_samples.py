import pytest
from pathlib import Path
from wformat.wformat import WFormat
import difflib


def test_new_samples():
    """
    Same workflow as required samples but on tests/sample/new:
      0. Clean stale *.formatted.cpp
      1. Format each original *.cpp (single dot) -> *.formatted.cpp
      2. Compare against *.correct.cpp
      3. Report unified diffs & idempotency issues
    """
    base_dir = Path(__file__).resolve().parents[1] / "sample" / "new"
    assert base_dir.is_dir(), f"Missing directory: {base_dir}"

    # 0) Cleanup
    for stale in base_dir.glob("*.formatted.cpp"):
        try:
            stale.unlink()
        except Exception:
            pass

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

        expected = correct_path.read_text(encoding="utf-8")
        if formatted != expected:
            diff_lines = difflib.unified_diff(
                expected.splitlines(keepends=True),
                formatted.splitlines(keepends=True),
                fromfile=f"{correct_path.name} (expected)",
                tofile=f"{formatted_path.name} (actual)",
                lineterm="",
            )
            diff_list = list(diff_lines)
            if len(diff_list) > 500:
                diff_list = diff_list[:500] + ["\n... (diff truncated)"]
            diffs.append(f"--- Diff for {src.name} ---\n" + "".join(diff_list))

        # Idempotency
        again = formatter.format_memory(formatted)
        if again != formatted:
            diffs.append(f"[NON-IDEMPOTENT] {src.name}")

    if diffs:
        for d in diffs:
            print(d)
        pytest.fail(
            f"{len(diffs)} issue(s) found across {processed} file(s). See diff output above.", pytrace=False
        )
