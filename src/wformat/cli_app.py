import argparse
import re
import sys
from pathlib import Path
from typing import Optional, Sequence

from importlib import metadata as _metadata

from wformat.wformat import WFormat
from wformat.daemon import WFormatDaemon
from wformat.utils import *  # noqa: F401,F403


def cli_app(argv: Optional[Sequence[str]] = None) -> int:

    if sys.version_info < (3, 0):
        sys.exit("This script requires Python 3 or higher.")

    wformat = WFormat()

    parser = argparse.ArgumentParser(
        description=(
            "tutorials:\n\n"
            "format all under the current folder: (-a/--against)\n"
            "   wformat -a origin/develop\n"
            "   → Recursively all C/C++ files diff with branch origin/develop.\n\n"
            "format all under the given folder: (-d/--dir)\n"
            "   wformat -d path/to/folder\n"
            "   → Recursively formats all C/C++ files under path/to/folder.\n\n"
            "format modified: (-m/--modified)\n"
            "   wformat -m\n"
            "   → Formats the modified files(not including staged) in your Git repository.\n\n"
            "format staged: (-s/--staged)\n"
            "   wformat -s\n"
            "   → Formats the staged files in your Git repository.\n\n"
            "format last N commits: (-c/--commits)\n"
            "   wformat -c N\n"
            "   → Formats files from last N commits in your Git repository.\n\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "paths",
        type=valid_path_in_args,
        nargs="*",
        help="All file paths to be formatted",
    )
    
    parser.add_argument(
        "-d",
        "--dir",
        type=valid_path_in_args,
        help="Run on file under which directory.",
    )
    parser.add_argument(
        "-a",
        "--against",
        metavar="BRANCH",
        help="Run auto format on files changed compared to BRANCH (git diff BRANCH...HEAD).",
    )
    parser.add_argument(
        "-m",
        "--modified",
        action="store_true",
        help="Run auto format on modified but not staged files in git.",
    )
    parser.add_argument(
        "-s",
        "--staged",
        action="store_true",
        help="Run auto format on staged files in git.",
    )
    parser.add_argument(
        "-c",
        "--commits",
        type=int,
        help="Run auto format on all files modified in the last N commits.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run auto format on all files which is child of current path.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only check the format correctness without changing files.",
    )
    parser.add_argument(
        "--serial",
        action="store_true",
        help="Run in serial mode or not. By default, script will use multi threading.",
    )
    parser.add_argument(
        "--ls",
        action="store_true",
        help="List all the files that matched given criteria to process and quit without processing them.",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read code from stdin and write formatted code to stdout (no banners).",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Run a persistent stdio server (JSON Lines) for IDE integration.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Show wformat version and exit.",
    )


    args = parser.parse_args(argv)

    if len(sys.argv) == 1:
        parser.print_help()
        return 0

    if args.version:
        try:
            ver = _metadata.version("wformat")
        except Exception:
            # fallback import (should already work) but just in case reuse package attr
            from wformat import __version__ as ver  # type: ignore
        print(ver)
        return 0

    if args.stdin:
        if sys.stdin.isatty():
            sys.stderr.write("[Error] --stdin used but no input piped\n")
            return 64  # EX_USAGE
        sys.exit(wformat.run_stdin_pipeline())

    if args.serve:
        sys.exit(WFormatDaemon(wformat).serve())

    file_paths = []

    if not sys.stdin.isatty():
        for line in sys.stdin:
            file_paths += [Path(line.strip())]

    if len(file_paths) == 0:
        file_paths = [Path(path) for path in args.paths]
        if len(file_paths) > 1000:
            print("[Warning] Could break console command length limit.")
            return 0

    if args.all:
        print(f"-- Will do recursive search for related files from ./")
        file_paths = search_files(Path("./"))
    elif args.dir:
        print(f"-- Will do recursive search for related files from {args.dir}")
        file_paths = search_files(Path(args.dir))
    elif args.against:
        print(f"-- Will search files changed compared to branch '{args.against}' (merge-base diff)")
        file_paths = get_files_changed_against_branch(args.against)
    elif len(sys.argv) == 1 or args.modified:
        print(f"-- Will search modified and not yet staged files by git")
        file_paths = get_modified_files()
    elif args.staged:
        print(f"-- Will search staged files by git")
        file_paths = get_staged_files()
    elif args.commits:
        print(f"-- Will search files changed in the last {args.commits} commits by git")
        file_paths = get_files_in_last_n_commits(args.commits)

    if len(file_paths) == 0:
        print("[Warning] No file found for formatting")
        return 0

    print(f"-- {len(file_paths)} file paths provided")

    file_paths = [
        file_path
        for file_path in file_paths
        if file_path.is_file()
        and file_path.exists()
        and re.match(r"^.*(?<!\.pb)\.(h|cpp)$", str(file_path.resolve()))
    ]

    if len(file_paths) == 0:
        print("[Warning] No file found for formatting")
        return 0

    print(f"-- {len(file_paths)} file paths matched criteria")

    if args.ls:
        for p in file_paths:
            print(p)
        return 0

    if args.check:
        wformat.format_inplace_many_mt(file_paths) if not args.serial else wformat.format_inplace_many(file_paths)
        return 0

    wformat.format_inplace_many_mt(file_paths) if not args.serial else wformat.format_inplace_many(file_paths)

    if args.modified or args.staged or args.commits or args.against:
        restage_files(file_paths)

    return 0
