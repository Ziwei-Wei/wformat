"""Utility script to clean/normalize formatter configuration files.

Run with:
    python scripts/self_clean_configs.py

It will invoke both clang-format and uncrustify self-clean logic provided by WFormat.
"""

from __future__ import annotations

from pathlib import Path
import sys

# Ensure the local 'src' directory is on sys.path when running from a fresh clone
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from wformat.wformat import WFormat


def main() -> int:
    print("-- Cleaning formatter configuration files ...")
    wf = WFormat()
    wf.self_clean_configs()
    print("-- Done.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
