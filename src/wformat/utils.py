import argparse
import subprocess
import os
import sys
from pathlib import Path
from typing import Sequence
import importlib.resources as ir


def wheel_bin_path(name: str) -> Path:
    # wformat/bin/<name>
    name = f"{name}.exe" if os.name == "nt" else name
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")) / "bin" / name
    return Path(ir.files("wformat") / "bin" / name)


def wheel_data_path(name: str) -> Path:
    # wformat/data/<name>
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")) / "data" / name
    return Path(ir.files("wformat") / "data" / name)


def valid_path_in_args(path: str) -> str:
    if os.path.exists(path):
        return path
    else:
        raise argparse.ArgumentTypeError(f"{path} does not exist.")


def restage_file(path: Path) -> None:
    """Restage a file in git."""
    try:
        subprocess.run(["git", "add", "--renormalize", str(path.resolve())], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[Error] Failed to restage {path}: {e}")


def restage_files(paths: Sequence[Path]) -> None:
    for path in paths:
        restage_file(path)


def get_modified_files() -> list[Path]:
    try:
        subprocess.run(["git", "--version"])
    except subprocess.CalledProcessError:
        print("[Warning] git not found!")
        return []

    result = subprocess.run(
        ["git", "ls-files", "-m", "--no-empty-directory"],
        capture_output=True,
        text=True,
    )
    modified_files = [Path("./" + line) for line in result.stdout.splitlines()]
    return modified_files


def get_staged_files() -> list[Path]:
    try:
        subprocess.run(["git", "--version"], check=True)
    except subprocess.CalledProcessError:
        print("[Warning] git not found!")
        return []

    result = subprocess.run(
        ["git", "diff", "--name-only", "--cached"],
        capture_output=True,
        text=True,
    )

    staged_files = [Path("./" + line) for line in result.stdout.splitlines()]
    return staged_files


def get_files_in_last_n_commits(n: int) -> list[Path]:
    try:
        subprocess.run(["git", "--version"], check=True)
    except subprocess.CalledProcessError:
        print("[Warning] git not found!")
        return []

    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"HEAD~{n}", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        print(f"[Error] Failed to get files from last {n} commits")
        return []

    return [Path("./" + line.strip()) for line in result.stdout.splitlines()]


def get_files_changed_against_branch(
    branch: str, use_merge_base: bool = True
) -> list[Path]:
    """Return files changed in the current HEAD compared to another branch.

    Parameters
    ----------
    branch: str
        The other branch to diff against.
    use_merge_base: bool
        If True (default) use three-dot syntax (branch...HEAD) which diffs
        against the merge base. If False, use two-dot (branch..HEAD).
    """
    try:
        subprocess.run(["git", "--version"], check=True)
    except subprocess.CalledProcessError:
        print("[Warning] git not found!")
        return []

    # Verify branch exists
    try:
        subprocess.run(
            ["git", "rev-parse", "--verify", branch], capture_output=True, check=True
        )
    except subprocess.CalledProcessError:
        print(f"[Error] Branch '{branch}' not found")
        return []

    diff_range = f"{branch}...HEAD" if use_merge_base else f"{branch}..HEAD"
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", diff_range],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        print(f"[Error] Failed to diff against branch '{branch}'")
        return []

    return [
        Path("./" + line.strip()) for line in result.stdout.splitlines() if line.strip()
    ]


def search_files(dir: Path) -> list[Path]:
    """Recursively gather all files under a directory."""
    return [p for p in dir.rglob("*") if p.is_file() and p.exists()]
