from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
from pathlib import Path
import shutil
import subprocess
import sys
import threading
from typing import Sequence

from wformat.clang_format import ClangFormat
from wformat.normalizer import *
from wformat.uncrustify import Uncrustify


def _get_formatted_path(file_path: Path) -> Path:
    return file_path.with_suffix(f".formatted{file_path.suffix}")


class WFormat:
    def __init__(self) -> None:
        self.clang_format: ClangFormat = ClangFormat()
        self.uncrustify: Uncrustify = Uncrustify()

    def format_memory(self, data: str) -> str:
        p1 = subprocess.Popen(
            self.clang_format.args_for_stdin(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=65536,
            text=False,
        )
        p2 = subprocess.Popen(
            self.uncrustify.args_for_stdin(),
            stdin=p1.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=65536,
            text=False,
        )
        p1.stdout.close()
        assert p1.stdin is not None
        p1.stdin.write(data.encode("utf-8"))
        p1.stdin.close()
        err1 = p1.stderr.read() if p1.stderr else b""
        out2, err2 = p2.communicate()
        rc1 = p1.wait()
        rc2 = p2.returncode
        if rc1 != 0:
            raise RuntimeError(
                err1.decode("utf-8", "replace") or f"clang-format failed ({rc1})"
            )
        if rc2 != 0:
            raise RuntimeError(
                err2.decode("utf-8", "replace") or f"uncrustify failed ({rc2})"
            )
        text = out2.decode("utf-8", "replace")
        text = fix_with_tree_sitter(text)
        text = normalize_integer_literal_in_memory(text)
        return text

    def run_stdin_pipeline(self) -> int:
        data = sys.stdin.read()
        text = self.format_memory(data)
        sys.stdout.write(text)
        sys.stdout.flush()
        return 0

    def format_inplace(self, file_path: Path) -> None:
        original_text = file_path.read_text(encoding="utf-8")
        formatted_text = self.format_memory(original_text)
        file_path.write_text(formatted_text, encoding="utf-8")
        self.uncrustify.clear_temp_files(file_path)

    def format_inplace_many(self, file_paths: Sequence[Path]) -> None:
        for p in file_paths:
            self.format_inplace(p)

    def format(self, file_path: Path) -> Path:
        formatted_file_path = _get_formatted_path(file_path)
        shutil.copyfile(file_path, formatted_file_path)
        self.format_inplace(formatted_file_path)
        return formatted_file_path

    def format_many(self, file_paths: Sequence[Path]) -> list[Path]:
        return [self.format(p) for p in file_paths]

    def format_inplace_many_mt(self, file_paths: Sequence[Path]) -> None:
        total_count = len(file_paths)
        if total_count == 0:
            print("-- No files to process")
            return
        cpu = multiprocessing.cpu_count()
        process_num = 1 if cpu <= 2 else (cpu - 1) // 2
        process_num = max(1, min(process_num, total_count))
        print(f"-- Detected {total_count} files to process")
        print(f"-- Will spawn {process_num} worker threads")
        progress_counter = 0
        progress_counter_lock = threading.Lock()

        def worker(p: Path) -> None:
            nonlocal progress_counter
            self.format_inplace(p)
            with progress_counter_lock:
                progress_counter += 1
                print(f"-- [{progress_counter}/{total_count}] {p}")

        error_counter = 0
        with ThreadPoolExecutor(max_workers=process_num) as executor:
            fut_to_path = {executor.submit(worker, p): p for p in file_paths}
            for fut in as_completed(fut_to_path):
                p = fut_to_path[fut]
                try:
                    fut.result()
                except Exception as e:
                    error_counter += 1
                    print(f"-- ERROR while processing {p}: {e!r}")
        if error_counter:
            print(f"-- Completed with {error_counter} error(s)")

    def self_clean_configs(self) -> None:
        self.clang_format.self_clean_config()
        self.uncrustify.self_clean_config()
