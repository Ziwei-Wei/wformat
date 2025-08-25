#!/usr/bin/env python3
"""
set_version.py - Safely update the version in pyproject.toml (PEP 621 style)

Usage:
    python scripts/set_version.py <version>

This script updates the [project] version in pyproject.toml.
"""
import sys
import toml

if len(sys.argv) != 2:
    print("Usage: python scripts/set_version.py <version>")
    sys.exit(1)

version = sys.argv[1]
pyproject = "pyproject.toml"

data = toml.load(pyproject)
if "project" not in data or "version" not in data["project"]:
    print("[project] or version key not found in pyproject.toml")
    sys.exit(1)

data["project"]["version"] = version
with open(pyproject, "w") as f:
    toml.dump(data, f)
print(f"Set version to {version} in {pyproject}")
