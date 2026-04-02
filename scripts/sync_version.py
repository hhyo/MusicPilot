#!/usr/bin/env python3
"""Synchronize the project version across Phase 0 artifacts."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
VERSION_PATTERN = re.compile(
    r"^(?P<version>\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.\-]+)?)$"
)

TARGETS = {
    "frontend_package": ROOT_DIR / "frontend" / "package.json",
    "runtime_package": ROOT_DIR / "plugin_runtime" / "package.json",
    "backend_pyproject": ROOT_DIR / "backend" / "pyproject.toml",
    "backend_init": ROOT_DIR / "backend" / "app" / "__init__.py",
    "runtime_init": ROOT_DIR / "plugin_runtime" / "plugins" / "musicpilot" / "__init__.py",
}


def require_version() -> str:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 scripts/sync_version.py <semver>")

    version = sys.argv[1].strip()
    if not VERSION_PATTERN.match(version):
        raise SystemExit(f"Invalid semantic version: {version}")
    return version


def update_json_version(path: Path, version: str) -> None:
    content = json.loads(path.read_text(encoding="utf-8"))
    content["version"] = version
    path.write_text(json.dumps(content, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def update_text_version(path: Path, pattern: str, replacement: str) -> None:
    content = path.read_text(encoding="utf-8")
    if re.search(pattern, content, flags=re.MULTILINE) is None:
        raise SystemExit(f"Could not update version in {path}")
    updated = re.sub(pattern, replacement, content, count=1, flags=re.MULTILINE)
    path.write_text(updated, encoding="utf-8")


def main() -> None:
    version = require_version()

    update_json_version(TARGETS["frontend_package"], version)
    update_json_version(TARGETS["runtime_package"], version)
    update_text_version(
        TARGETS["backend_pyproject"],
        r'^version = ".*"$',
        f'version = "{version}"',
    )
    update_text_version(
        TARGETS["backend_init"],
        r'^__version__ = ".*"$',
        f'__version__ = "{version}"',
    )
    update_text_version(
        TARGETS["runtime_init"],
        r'^__version__ = ".*"$',
        f'__version__ = "{version}"',
    )

    print(f"Synchronized MusicPilot version to {version}")


if __name__ == "__main__":
    main()
