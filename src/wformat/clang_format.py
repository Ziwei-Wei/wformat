from pathlib import Path
import subprocess
import traceback

from wformat.utils import wheel_bin_path, wheel_data_path


class ClangFormat:
    """Thin wrapper around clang-format with packaged executable and config"""

    def __init__(self):
        self.exe_path = wheel_bin_path("clang-format")
        self.config_path = wheel_data_path(".clang-format")

    def print_info(self) -> None:
        """Print information about the clang-format executable and config."""
        print()
        print(f"Clang-format executable: {self.exe_path}")
        print(f"Clang-format config: {self.config_path}")
        print("Using clang-format version:")
        subprocess.run([str(self.exe_path), "--version"], check=True)

    def format(self, file_path: Path) -> None:
        """format a given file in place"""
        subprocess.run(
            [
                str(self.exe_path),
                "-i",
                f"-style=file:{self.config_path}",
                str(file_path),
            ],
            check=True,
        )

    def format_data(self, data: str) -> str:
        """
        Format in-memory source code and return the formatted text.

        Uses the packaged .clang-format by setting -style=file and
        -assume-filename to a dummy file next to that config so clang-format
        can discover it when reading from stdin.
        """
        res = subprocess.run(
            self.args_for_stdin(),
            input=data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
            encoding="utf-8",
        )
        return res.stdout

    def args_for_stdin(self) -> list[str]:
        # Pretend the code comes from a .cpp file next to the config so
        # '-style=file' finds the config directory.
        assume_file = str(self.config_path.parent / "dummy.cpp")
        return [
            str(self.exe_path),
            f"-style=file:{self.config_path}",
            f"-assume-filename={assume_file}",
        ]

    def self_clean_config(self) -> None:
        """
        Regenerate the config with documentation comments
        """

        try:
            res = subprocess.run(
                [str(self.exe_path), f"-style=file:{self.config_path}", "-dump-config"],
                check=True,
                capture_output=True,
                text=True,
            )
            new_config_path = self.config_path.parent / f"{self.config_path}.new"
            new_config_path.write_text(res.stdout, encoding="utf-8")
            new_config_path.replace(self.config_path)

        except Exception:
            print(traceback.format_exc())
            raise
