#!/usr/bin/env python3
"""Assemble frontend and backend artifacts into plugin_runtime for Phase 0."""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"
BACKEND_APP = ROOT_DIR / "backend" / "app"
BACKEND_REQUIREMENTS = ROOT_DIR / "backend" / "requirements.txt"
PLUGIN_DIR = ROOT_DIR / "plugin_runtime" / "plugins" / "musicpilot"
STATIC_DIR = PLUGIN_DIR / "static"

COPYABLE_BACKEND_ITEMS = [
    "__init__.py",
    "main.py",
    "api",
    "core",
    "schemas",
    "services",
    "adapters",
    "models",
    "repositories",
    "tasks",
]


def reset_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def copy_backend() -> None:
    for item_name in COPYABLE_BACKEND_ITEMS:
        source = BACKEND_APP / item_name
        target = PLUGIN_DIR / item_name

        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()

        if source.is_dir():
            shutil.copytree(source, target)
        elif source.is_file():
            shutil.copy2(source, target)

    shutil.copy2(BACKEND_REQUIREMENTS, PLUGIN_DIR / "requirements.txt")


def copy_frontend() -> None:
    if not FRONTEND_DIST.exists():
        raise FileNotFoundError(
            "frontend/dist does not exist. Run `pnpm build` in frontend before packaging."
        )

    reset_directory(STATIC_DIR)

    for item in FRONTEND_DIST.iterdir():
        target = STATIC_DIR / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def main() -> None:
    copy_backend()
    copy_frontend()
    print("Packaged MusicPilot placeholder runtime into plugin_runtime/plugins/musicpilot")


if __name__ == "__main__":
    main()

