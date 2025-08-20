from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
from pathlib import Path
import shutil
import subprocess
import sys
import threading
from typing import List

from rd_format.clang_format import ClangFormat
from rd_format.utils import handle_integer_literal, handle_integer_literal_in_data
from rd_format.uncrustify import Uncrustify


class RdFormat:
    def __init__(self):
        self.clang_format = ClangFormat()
        self.uncrustify = Uncrustify()

    def run_stdin_pipeline(self) -> int:
        """
        Stream stdin -> clang-format -> uncrustify -> stdout.
        Returns the exit code (0 on success).
        """
        p1 = subprocess.Popen(
            self.clang_format.args_for_stdin(),
            stdin=sys.stdin.buffer,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=65536,
            text=False,
        )
        
        p2 = subprocess.Popen(
            self.uncrustify.args_for_stdin(),
            stdin=p1.stdout,
            stdout=sys.stdout.buffer,
            stderr=subprocess.PIPE,
            bufsize=65536,
            text=False,
        )

        # Ensure p1 sees a closed pipe if p2 exits early
        p1.stdout.close()

        # p2 writes directly to stdout; gather only stderr/return codes
        _, err2_b = p2.communicate()
        err1_b = p1.stderr.read()
        rc1 = p1.wait()
        rc2 = p2.returncode
        
        if rc1 != 0:
            sys.stderr.write(err1_b.decode("utf-8", "replace"))
            return rc1
        if rc2 != 0:
            sys.stderr.write(err2_b.decode("utf-8", "replace"))
            return rc2
        return 0
    
    def format_memory(self, data: str) -> str:
        """
        str -> clang-format -> uncrustify -> str.
        Returns the formatted text.
        """
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
        
        # Ensure p1 sees a closed pipe if p2 exits early
        p1.stdout.close()
        
        p1.stdin.write(data.encode("utf-8"))
        p1.stdin.close()

        # p2 writes directly to stdout
        out_b, err2_b = p2.communicate()
        err1_b = p1.stderr.read()
        rc1 = p1.wait()
        rc2 = p2.returncode

        if rc1 != 0:
            raise RuntimeError(err1_b.decode("utf-8", "replace") or f"clang-format failed ({rc1})")
        if rc2 != 0:
            raise RuntimeError(err2_b.decode("utf-8", "replace") or f"uncrustify failed ({rc2})")

        return out_b.decode("utf-8", "replace")

    # --- single-file, in-place ---
    def format_inplace(self, file_path: Path) -> None:
        """
        Apply all formatters directly on a file in place.
        """
        self.clang_format.format(file_path)
        handle_integer_literal(file_path)
        self.uncrustify.format(file_path)
        self.uncrustify.clear_temp_files(file_path)

    # --- many-files, in-place ---
    def format_inplace_many(self, file_paths: List[Path]) -> None:
        """Run in-place formatting on multiple files."""
        for p in file_paths:
            self.format_inplace(p)

    # --- single-file, copy -> result then format ---
    def format(self, file_path: Path) -> Path:
        """
        Create and format xxx.formatted.cpp copied from xxx.cpp
        """
        formatted_file_path = _get_formatted_path(file_path)
        shutil.copyfile(file_path, formatted_file_path)
        self.format_inplace(formatted_file_path)
        return formatted_file_path

    # --- many-files, copy -> *.formatted.<ext> then format ---
    def format_many(self, file_paths: List[Path]) -> List[Path]:
        """Create and format xxx.formatted.cpp copied from any given xxx.cpp"""
        return [self.format(p) for p in file_paths]

    def format_inplace_many_mt(self, file_paths: List[Path]) -> None:
        """
        Multi-threaded formatting of many files.
        Spawns a thread pool, schedules self.format on each file, and
        prints progress as each file completes.
        """
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

        def worker(p: Path):
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
        else:
            print("-- All files processed successfully")

    def check(self, file_path: Path) -> bool:
        """Check if a file is formatted correctly."""
        self.format(file_path)
        formatted_file_path = _get_formatted_path(file_path)
        with open(file_path, "r", encoding="utf-8") as original_file:
            original_content = original_file.read()
        with open(formatted_file_path, "r", encoding="utf-8") as formatted_file:
            formatted_content = formatted_file.read()
        _clear_formatted_file(formatted_file_path)
        return original_content == formatted_content

    def check_mt(self, file_paths: List[Path]) -> bool:
        """
        Multi-threaded check: verify if many files are correctly formatted.
        Returns True if all files are correctly formatted, False otherwise.
        """
        total_count = len(file_paths)
        if total_count == 0:
            print("-- No files to check")
            return True

        cpu = multiprocessing.cpu_count()
        process_num = 1 if cpu <= 2 else (cpu - 1) // 2

        print(f"-- Detected {total_count} files to check")
        print(f"-- Will spawn {process_num} worker threads")

        counter = 0
        counter_lock = threading.Lock()
        errors = 0
        bad_files = []

        def worker(p: Path) -> bool:
            nonlocal counter
            ok = self.check(p)
            with counter_lock:
                counter += 1
                status = "OK" if ok else "NOT FORMATTED"
                print(f"-- [{counter}/{total_count}] {p} -> {status}")
            return ok

        from concurrent.futures import ThreadPoolExecutor, as_completed

        with ThreadPoolExecutor(max_workers=process_num) as executor:
            fut_to_path = {executor.submit(worker, p): p for p in file_paths}
            for fut in as_completed(fut_to_path):
                p = fut_to_path[fut]
                try:
                    ok = fut.result()
                    if not ok:
                        errors += 1
                        bad_files.append(p)
                except Exception as e:
                    errors += 1
                    bad_files.append(p)
                    print(f"-- ERROR while checking {p}: {e!r}")

        if errors:
            print(f"-- {errors} file(s) not formatted properly:")
            for bf in bad_files:
                print(f"   {bf}")
            return False
        else:
            print("-- All files are correctly formatted")
            return True


def _get_formatted_path(p: Path) -> Path:
    """xxx.cpp -> xxx.formatted.cpp"""
    return p.with_name(f"{p.stem}.formatted{p.suffix}")


def _clear_formatted_file(p: Path) -> None:
    formatted_file_path = _get_formatted_path(p)
    formatted_file_path.unlink(True)
