"""wformat package public API.

Exposes the package version as __version__.
"""

from __future__ import annotations

from importlib import metadata as _metadata

try:  # Prefer distribution metadata when installed
    __version__ = _metadata.version("wformat")
except Exception:  # Fallback to parsing pyproject.toml in editable/source checkout
    try:
        import tomllib  # Python 3.11+
    except ModuleNotFoundError:  # pragma: no cover - earlier Python fallback
        tomllib = None  # type: ignore
    if tomllib:  # pragma: no branch
        import pathlib

        pyproject = pathlib.Path(__file__).resolve().parents[1] / "pyproject.toml"
        if pyproject.is_file():
            try:
                data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
                __version__ = data.get("project", {}).get("version", "0.0.0+unknown")  # type: ignore
            except Exception:  # pragma: no cover - very unlikely
                __version__ = "0.0.0+unknown"
        else:
            __version__ = "0.0.0+unknown"
    else:
        __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
