# rd-format.spec
# Build:  pyinstaller -y --clean rd-format.spec
# Output: dist/rd-format/rd-format(.exe)  (+ files in dist/rd-format/)

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

# Variables
APP_NAME = "rd-format"
MODULE_NAME = "rd_format"
ROOT = Path(os.getcwd()).resolve()
SRC_DIR = ROOT / "src"
PKG_DIR = SRC_DIR / MODULE_NAME
IS_WINDOWS = os.name == "nt"

# Entry script for your CLI. Change if your entry is different.
ENTRY_SCRIPTS = [str(SRC_DIR / "rd_format_launcher.py")]


# External tools + configs to bundle
CLANG_NAME = "clang-format.exe" if IS_WINDOWS else "clang-format"
UNCRUSTIFY_NAME = "uncrustify.exe" if IS_WINDOWS else "uncrustify"

CLANG_FORMAT_EXE = PKG_DIR / "bin" / CLANG_NAME
UNCRUSTIFY_EXE = PKG_DIR / "bin" / UNCRUSTIFY_NAME

CLANG_CONFIG = PKG_DIR / "data" / ".clang-format"
UNCRUSTIFY_CONFIG = PKG_DIR / "data" / "uncrustify.cfg"

# Tell PyInstaller where to put the auxiliary files inside the bundle.
binaries = [
    (str(CLANG_FORMAT_EXE), "bin"),
    (str(UNCRUSTIFY_EXE), "bin"),
]

datas = [
    (str(CLANG_CONFIG), "data"),
    (str(UNCRUSTIFY_CONFIG), "data"),
]

a = Analysis(
    scripts=ENTRY_SCRIPTS,
    pathex=[str(SRC_DIR)],
    binaries=binaries,
    datas=datas,
    hiddenimports=collect_submodules(MODULE_NAME),
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "turtledemo",
        "unittest",
        "test",
        "pydoc_data",
        "distutils",
        "lib2to3",
        "ensurepip",
        "venv",
    ],
    noarchive=True,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name=APP_NAME,
    console=True,
    debug=False,
    bootloader_ignore_signals=False,
    strip=(IS_WINDOWS == False),
    upx=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=(IS_WINDOWS == False),
    upx=False,
    name=APP_NAME,
)

# Remove the stray launcher that EXE leaves at dist/rd-format(.exe)
top_level = ROOT / "dist" / (APP_NAME + (".exe" if IS_WINDOWS else ""))
top_level.unlink(missing_ok=True)