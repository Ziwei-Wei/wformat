# wformat.spec
# Build:  pyinstaller -y --clean wformat.spec
# Output: dist/wformat/wformat(.exe)

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

ROOT = Path(os.getcwd()).resolve()
IS_WINDOWS = os.name == "nt"

APP_NAME = "wformat"
EXE_NAME = APP_NAME + (".exe" if IS_WINDOWS else "")
TMP_EXE_NAME = APP_NAME + ".tmp" + (".exe" if IS_WINDOWS else "")
MODULE_NAME = APP_NAME
SRC_DIR = ROOT / "src"
PKG_DIR = SRC_DIR / MODULE_NAME
ENTRY_SCRIPT = str(SRC_DIR / f"{APP_NAME}_launcher.py")

CLANG_EXE_NAME = "clang-format" + (".exe" if IS_WINDOWS else "")
UNCRUSTIFY_EXE_NAME = "uncrustify" + (".exe" if IS_WINDOWS else "")
CLANG_FORMAT_EXE = PKG_DIR / "bin" / CLANG_EXE_NAME
UNCRUSTIFY_EXE = PKG_DIR / "bin" / UNCRUSTIFY_EXE_NAME
CLANG_CONFIG = PKG_DIR / "data" / ".clang-format"
UNCRUSTIFY_CONFIG = PKG_DIR / "data" / "uncrustify.cfg"

binaries = [
    (str(CLANG_FORMAT_EXE), "bin"),
    (str(UNCRUSTIFY_EXE), "bin"),
]

datas = [
    (str(CLANG_CONFIG), "data"),
    (str(UNCRUSTIFY_CONFIG), "data"),
]

a = Analysis(
    scripts=[ENTRY_SCRIPT],
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
    name=TMP_EXE_NAME,
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

(ROOT / "dist" / TMP_EXE_NAME).unlink(missing_ok=True)
(ROOT / "dist" / APP_NAME / TMP_EXE_NAME).rename(ROOT / "dist" / APP_NAME / EXE_NAME)