import argparse
from asyncio import subprocess
from importlib.metadata import files
import os
import re
import sys
from pathlib import Path
import traceback
from typing import List
import importlib.resources as ir

INTEGER_LITERAL_PATTERN = re.compile(
    r"\b((0[bB]([01][01']*[01]|[01]+))|(0[xX]([\da-fA-F][\da-fA-F']*[\da-fA-F]|[\da-fA-F]+))|(0([0-7][0-7']*[0-7]|[0-7]+))|([1-9](\d[\d']*\d|\d*)))([uU]?[lL]{0,2}|[lL]{0,2}[uU]?)?\b"
)


def handle_integer_literal(file_path: Path, upper_case: bool = True) -> None:
    try:
        with open(file_path, "r+", encoding="utf-8") as file:
            code = file.read()
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(handle_integer_literal_in_data(code, upper_case))
    except Exception:
        print(traceback.format_exc())
        
def handle_integer_literal_in_data(data: str, upper_case: bool = True) -> str:
    def replace(match: re.Match[str]):
            update = match.group(0)
            update = update.upper() if upper_case else update.lower()
            if len(update) > 1 and update[0] == "0":
                update = update[0] + update[1].lower() + update[2:]
            if data[match.start() - 1] == "&":
                update = " " + update
            return update

    return INTEGER_LITERAL_PATTERN.sub(repl=replace, string=data)

def wheel_bin_path(name: str) -> Path:
    # rd_format/bin/<name>
    name = f"{name}.exe" if os.name == "nt" else name
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")) / "bin" / name
    return Path(ir.files("rd_format") / "bin" / name)


def wheel_data_path(name: str) -> Path:
    # rd_format/data/<name>
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")) / "data" / name
    return Path(ir.files("rd_format") / "data" / name)


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


def restage_files(paths: List[Path]) -> None:
    for path in paths:
        restage_file(path)


def get_modified_files() -> List[Path]:
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


def get_staged_files() -> List[Path]:
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


def get_files_in_last_n_commits(n: int) -> List[Path]:
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


def filter_path_by_path(
    file_paths: List[Path], include_paths: List[Path], exclude_paths: List[Path]
) -> List[Path]:
    filtered_paths = []
    for file_path in file_paths:
        if any(
            file_path.resolve().is_relative_to(include_path.resolve())
            for include_path in include_paths
        ) and all(
            not file_path.resolve().is_relative_to(exclude_path.resolve())
            for exclude_path in exclude_paths
        ):
            filtered_paths += [file_path]
    return filtered_paths


def search_files(dir: Path) -> list[Path]:
    return [path for path in list(dir.rglob("*")) if path.is_file() and path.exists()]


def find_file(name: str, dir: Path = Path(".")) -> Path:
    for file in dir.rglob(name):
        if file.is_file() and file.exists():
            return file
    return None
