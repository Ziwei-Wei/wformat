from pathlib import Path
import subprocess
import traceback

from wformat.utils import wheel_bin_path, wheel_data_path


class Uncrustify:
    """Thin wrapper around uncrustify with packaged executable and config"""

    def __init__(self):
        self.exe_path = wheel_bin_path("uncrustify")
        self.config_path = wheel_data_path("uncrustify.cfg")

    def print_info(self) -> None:
        """Print information about the uncrustify executable and config."""
        print(f"Uncrustify executable: {self.exe_path}")
        print(f"Uncrustify config: {self.config_path}")
        print("Using uncrustify version:")
        subprocess.run(
            [str(self.exe_path), "-c", str(self.config_path), "--version"], check=True
        )
        print()

    def format(self, file_path: Path, round: int = 1) -> None:
        """format a given file in place, multiple times if specified"""
        # note unlike clang-format, uncrustify do not guarantee the stability of end result after a single run
        # use multiple runs to keep the result consistent
        for _ in range(round):
            subprocess.run(
                [
                    self.exe_path,
                    "-q",
                    "-l",
                    "CPP",
                    "-c",
                    self.config_path,
                    "--replace",
                    "--no-backup",
                    file_path,
                ],
                check=True,
            )

    def format_data(self, data: str) -> str:
        """
        Format in-memory source code and return the formatted text.
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
        return [
            self.exe_path,
            "-q",
            "-l", 
            "CPP",
            "-c",
            self.config_path,
        ]

    def clear_temp_files(self, file_path: Path) -> None:
        """Remove the .uncrustify temp file if it exists."""
        temp_file_path = file_path.with_suffix(file_path.suffix + ".uncrustify")
        temp_file_path.unlink(missing_ok=True)

    def self_clean_config(self) -> None:
        """
        Regenerate the config with documentation comments
        """

        try:
            res = subprocess.run(
                [self.exe_path, "-c", self.config_path, f"--update-config-with-doc"],
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
