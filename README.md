# WFormat

Opinionated code formatter for C++ code.

## Availability

limit: only support Format Document in IDEs for now

### Visual Studio Code

- [x] win-x64
- [ ] win-arm64
- [x] macos
- [x] linux-64
- [ ] linux-arm64

### Visual Studio

- [x] win-x64
- [ ] win-arm64

### XCode

- [ ] macos

### Python Package Index(PyPI)

- [x] win-x64
- [ ] win-arm64
- [x] macos
- [ ] linux-64
- [ ] linux-arm64

## Tutorials

### Use Visual Studio Code Extension

Install ```wformat``` from extension market

In any C++ file, Press ```ctrl + alt + P``` to bring up the command menu

Type ```Format Document With...``` select ```Config Default Formatter...``` pick ```wformat```

Next time you call ```Format Document```, vscode will use wformat

### Use Visual Studio Extension

Install ```wformat``` from extension market

By default, you can only click ```Run WFormat``` in your Right Click Menu to format on the file

You can find ```wformat.General```(or search ```wformat```) in ```Tools > Options``` menu

By change ```Override default formatter``` to ```True```, you can use Format Document(```ctrl + K```, ```ctrl + D```) with wformat instead

### Use as console app from ```Python Package Index (PyPI)```

Run ```pip install wformat```

Run ```wformat``` or ```wformat -h``` to access the docs

```default
> wformat
overview: Opinionated code formatter for C++ code

usage: wformat [-h] [-a] [-d DIR] [-m] [-s] [-c COMMITS] [--check] [--serial] [--ls] [--stdin] [--serve] [paths ...]

tutorials:

format all under the current folder: (-a/--all)
   wformat -a
   → Recursively formats all C/C++ files under the current folder.

format all under the given folder: (-d/--dir)
   wformat -d path/to/folder
   → Recursively formats all C/C++ files under path/to/folder.

format modified: (-m/--modified)
   wformat -m
   → Formats the modified files(not including staged) in your Git repository.

format staged: (-s/--staged)
   wformat -s
   → Formats the staged files in your Git repository.

format last N commits: (-c/--commits)
   wformat -c N
   → Formats files from last N commits in your Git repository.

positional arguments:
  paths                 All file paths to be formatted

options:
  -h, --help            show this help message and exit
  -a, --all             Run auto format on all files which is child of current path.
  -d, --dir DIR         Run on file under which directory.
  -m, --modified        Run auto format on modified but not staged files in git.
  -s, --staged          Run auto format on staged files in git.
  -c, --commits COMMITS
                        Run auto format on all files modified in the last N commits.
  --check               Only check the format correctness without changing files.
  --serial              Run in serial mode or not. By default, script will use multi threading.
  --ls                  List all the files that matched given criteria to process and quit without processing them.
  --stdin               Read code from stdin and write formatted code to stdout (no banners).
  --serve               Run a persistent stdio server (JSON Lines) for IDE integration.
```
