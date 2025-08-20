# C/C++ Code Standard for rdcore-workshop

*Code Standard/Policy Maker: Elton Saul <eltons@microsoft.com>*

*Tool/Script/Config Maintainer: Ziwei Wei <ziweiwei@microsoft.com>*

## Install Tutorial(make sure you have python installed)

run ```pip install rd-format```

## Usage Tutorial

### Run ```rd-format``` or ```rd-format -h``` in your commandline to access the docs of this script

```default
> rd-format
overview: Opinionated code formatter for C++ code in RdCore

usage: rd-format [-h] [-a] [-d DIR] [-m] [-s] [-c COMMITS] [--check] [--serial] [--ls] [--stdin] [--serve] [paths ...]

tutorials:

format all under the current folder: (-a/--all)
   rd-format -a
   → Recursively formats all C/C++ files under the current folder.

format all under the given folder: (-d/--dir)
   rd-format -d path/to/folder
   → Recursively formats all C/C++ files under path/to/folder.

format modified: (-m/--modified)
   rd-format -m
   → Formats the modified files(not including staged) in your Git repository.

format staged: (-s/--staged)
   rd-format -s
   → Formats the staged files in your Git repository.

format last N commits: (-c/--commits)
   rd-format -c N
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

## IDE Integration

### Visual Studio Code(ready)

### Visual Studio(needs future work)

### XCode(needs future work)

## Contribute

### Setup rd-format repo

### Get tests running

### Distribute to PyPi and vscode market place

### Use Coding Agent to keep improving this

## Important Q&A for developers

### Why use both ```clang-format``` and ```uncrustify``` as formatter?

**A: There is no perfect tools in C/C++ toolchain. ```clang-format``` is better at general code structure and grammar enforcement related to the code and ```uncrustify``` is better at tweaking details of code in space, indent, and new-line insert level. Using ```clang-format``` to format files on first pass, then apply ```uncrustify``` will let use all possible rules at will.**

### Why the ```uncrustify``` will be run multiple times on same file in the script?

**A: Because ```uncrustify``` is basically a incremental formatter it does not guarantee that the formatted file can not be formatted further. It is necessary to run it multiple time to ensure the correctness.**

### Update uncrustify config with full docs

run the following code after you updated the ```uncrustify.cfg```

```shell
uncrustify -c ./uncrustify.cfg --update-config-with-doc > ./uncrustify.new.cfg
mv ./uncrustify.new.cfg ./uncrustify.cfg
```

```shell
pyinstaller -y --clean rd-format.spec
```
