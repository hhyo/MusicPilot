"""MusicPilot runtime-capable package.

用途：
- 作为本地 FastAPI 工程的包根
- 作为 plugin_runtime 装配后的插件包根
- 保留最小版本号和插件元信息

注意：
- 当前阶段不实现真实 MoviePilot 插件注册逻辑
- 当前阶段不声明不存在的宿主 API
- 后续仅在宿主契约明确后补真实入口与注册信息
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from app.plugins import _PluginBase as _HostPluginBase
except Exception:  # pragma: no cover - only available inside MoviePilot host runtime
    _HostPluginBase = None

__version__ = "0.1.0"
PLUGIN_NAME = "MusicPilot"
PLUGIN_DESCRIPTION = "Music discovery, metadata, subscriptions, and organize workspace for MoviePilot."


def _bootstrap_plugin_storage() -> None:
    from .services.metadata import bootstrap_metadata_storage

    bootstrap_metadata_storage()


def _build_plugin_api_manifest() -> list[dict[str, Any]]:
    from .api.router import plugin_api_router

    apis: list[dict[str, Any]] = []
    for route in plugin_api_router.routes:
        path = getattr(route, "path", None)
        endpoint = getattr(route, "endpoint", None)
        methods = sorted(
            method for method in (getattr(route, "methods", None) or set())
            if method not in {"HEAD", "OPTIONS"}
        )
        if not path or not endpoint or not methods:
            continue
        apis.append(
            {
                "path": path,
                "endpoint": endpoint,
                "methods": methods,
                "summary": getattr(route, "summary", None) or getattr(route, "name", path),
                "description": getattr(route, "description", None) or "",
            }
        )
    return apis


def _resolve_remote_dist_path() -> str:
    remotes_dir = Path(__file__).resolve().parent / "static" / "remotes"
    if remotes_dir.exists():
        remote_versions = sorted(
            path.name for path in remotes_dir.iterdir()
            if path.is_dir() and (path / "remoteEntry.js").exists()
        )
        if remote_versions:
            return f"static/remotes/{remote_versions[-1]}"
    return "static/assets"


if _HostPluginBase is not None:
    class musicpilot(_HostPluginBase):
        """Minimal MoviePilot plugin entry for loading MusicPilot runtime in-process."""

        plugin_name = PLUGIN_NAME
        plugin_desc = PLUGIN_DESCRIPTION
        plugin_version = __version__
        plugin_order = 999

        def __init__(self):
            super().__init__()
            self._config: dict[str, Any] = {}
            self._enabled = True
            self._storage_bootstrapped = False

        def init_plugin(self, config: dict = None):
            self._config = config or {}
            self._enabled = bool(self._config.get("enabled", True))
            if self._enabled and not self._storage_bootstrapped:
                _bootstrap_plugin_storage()
                self._storage_bootstrapped = True

        def get_state(self) -> bool:
            return self._enabled

        def get_api(self) -> list[dict[str, Any]]:
            if not self._enabled:
                return []
            return _build_plugin_api_manifest()

        def get_form(self):
            return [], {"enabled": True}

        @staticmethod
        def get_render_mode():
            return "vue", _resolve_remote_dist_path()

        def get_page(self):
            return None

        @staticmethod
        def get_dashboard_meta():
            return [{"key": "home", "name": "MusicPilot"}]

        def get_dashboard(self, key: str = "", **kwargs):
            del kwargs
            if key and key != "home":
                return {"cols": 12, "md": 6, "lg": 4}, {
                    "border": False,
                    "title": PLUGIN_NAME,
                    "subtitle": "音乐发现、元数据与整理工作台",
                }, None
            return {"cols": 12, "md": 6, "lg": 4}, {
                "border": False,
                "title": PLUGIN_NAME,
                "subtitle": "音乐发现、元数据与整理工作台",
            }, None

        def stop_service(self):
            return None
