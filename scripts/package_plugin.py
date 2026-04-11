#!/usr/bin/env python3
"""Assemble frontend and backend artifacts into plugin_runtime for Phase 0."""

from __future__ import annotations

import shutil
from hashlib import sha256
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

    remote_entry_path = STATIC_DIR / "assets" / "remoteEntry.js"
    normalize_remote_entry_asset_paths(remote_entry_path)
    publish_versioned_remote_bundle(STATIC_DIR)


def normalize_remote_entry_asset_paths(remote_entry_path: Path) -> None:
    """Normalize vite federation asset paths for host-served plugin remotes.

    `@originjs/vite-plugin-federation` currently emits `remoteEntry.js` that uses
    `base: './'` in a way that breaks when the remote is served from a nested host
    path like `/api/v1/plugin/file/.../assets/remoteEntry.js`.

    Two concrete issues appear in MoviePilot:
    - CSS hrefs become `.../assets./chunk.css`
    - exposed JS chunks become `.../assets/assets/chunk.js`

    Packaging is the narrowest place to correct this for the plugin runtime while
    keeping the standalone frontend dev experience unchanged.
    """
    if not remote_entry_path.exists():
        return

    original = remote_entry_path.read_text(encoding="utf-8")
    normalized = (
        original
        .replace("a='./';", "a='';")
        .replace('y("./assets/', 'y("./')
        .replace('w("./assets/', 'w("./')
        .replace('b("./assets/', 'b("./')
    )

    if normalized != original:
        remote_entry_path.write_text(normalized, encoding="utf-8")


def publish_versioned_remote_bundle(static_dir: Path) -> None:
    """Copy federated assets into a content-addressed remote directory.

    This changes the host remote URL on every relevant build output change and
    avoids browsers reusing a stale `remoteEntry.js` from cache.
    """
    assets_dir = static_dir / "assets"
    remote_entry_path = assets_dir / "remoteEntry.js"
    if not remote_entry_path.exists():
        return

    remotes_dir = static_dir / "remotes"
    reset_directory(remotes_dir)

    remote_version = sha256(remote_entry_path.read_bytes()).hexdigest()[:12]
    target_dir = remotes_dir / remote_version
    shutil.copytree(assets_dir, target_dir)


def main() -> None:
    copy_backend()
    copy_frontend()
    print("Packaged MusicPilot placeholder runtime into plugin_runtime/plugins/musicpilot")


if __name__ == "__main__":
    main()
