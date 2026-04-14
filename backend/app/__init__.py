"""MusicPilot runtime-capable package.

用途：
- 作为本地 FastAPI 工程的包根
- 作为 plugin_runtime 装配后的插件包根
- 保留最小版本号和插件元信息

说明：
- 在 MoviePilot 宿主内通过插件入口注册 API、侧边栏、仪表盘和调度服务
- 在独立 FastAPI 模式下保留本地开发入口
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
from pathlib import Path
from typing import Any

try:
    from app.plugins import _PluginBase as _HostPluginBase
except Exception:  # pragma: no cover - only available inside MoviePilot host runtime
    _HostPluginBase = None

__version__ = "0.1.0"
PLUGIN_NAME = "MusicPilot"
PLUGIN_DESCRIPTION = "Music discovery, metadata, subscriptions, and organize workspace for MoviePilot."
logger = logging.getLogger("musicpilot.plugin")


def _bootstrap_plugin_storage() -> None:
    from .startup.bootstrap import bootstrap_runtime_storage

    bootstrap_runtime_storage()


def _load_local_module(relative_name: str):
    package_name = __package__
    if package_name:
        try:
            return importlib.import_module(f"{package_name}.{relative_name}")
        except ModuleNotFoundError:
            pass
    module_path = Path(__file__).resolve().parent / Path(*relative_name.split("."))
    module_file = module_path.with_suffix(".py")
    spec = importlib.util.spec_from_file_location(
        f"_musicpilot_local_{relative_name.replace('.', '_')}",
        module_file,
    )
    if spec is None or spec.loader is None:
        raise ModuleNotFoundError(relative_name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def _scheduler_seconds(module: Any, attr: str, fallback: int) -> int:
    func = getattr(module, attr, None)
    if callable(func):
        return int(func())
    return fallback


def _resolve_remote_dist_path() -> str:
    remotes_dir = Path(__file__).resolve().parent / "static" / "remotes"
    if remotes_dir.exists():
        remote_dirs = [
            path for path in remotes_dir.iterdir()
            if path.is_dir() and (path / "remoteEntry.js").exists()
        ]
        if remote_dirs:
            latest_remote = max(remote_dirs, key=lambda path: path.stat().st_mtime)
            return f"static/remotes/{latest_remote.name}"
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

        def get_service(self) -> list[dict[str, Any]]:
            settings_module = _load_local_module("core.config")
            scheduler_module = _load_local_module("startup.scheduler")
            if not self._enabled or not settings_module.settings.subscription_scheduler_enabled:
                return []
            return [
                {
                    "id": "music-subscription-scheduler",
                    "name": "MusicPilot 订阅调度",
                    "trigger": "interval",
                    "func": self.run_scheduler_once,
                    "kwargs": {
                        "seconds": _scheduler_seconds(
                            scheduler_module,
                            "subscription_scheduler_interval_seconds",
                            max(1, int(round(settings_module.settings.subscription_scheduler_poll_seconds))),
                        )
                    },
                },
                {
                    "id": "music-chart-refresh",
                    "name": "MusicPilot 榜单刷新",
                    "trigger": "interval",
                    "func": self.run_chart_refresh_once,
                    "kwargs": {
                        "minutes": _scheduler_seconds(
                            scheduler_module,
                            "chart_refresh_interval_minutes",
                            max(1, int(round(settings_module.settings.chart_refresh_interval_minutes))),
                        )
                    },
                },
                {
                    "id": "music-transfer",
                    "name": "MusicPilot 下载整理",
                    "trigger": "interval",
                    "func": self.run_transfer_once,
                    "kwargs": {
                        "seconds": _scheduler_seconds(
                            scheduler_module,
                            "transfer_interval_seconds",
                            max(60, int(round(settings_module.settings.host_handoff_retry_interval_seconds))),
                        )
                    },
                }
            ]

        def get_form(self):
            return [], {"enabled": True}

        @staticmethod
        def get_render_mode():
            return "vue", _resolve_remote_dist_path()

        def get_page(self):
            return None

        @staticmethod
        def get_sidebar_nav():
            return [
                {
                    "nav_key": "main",
                    "title": "MusicPilot",
                    "icon": "mdi-music-note-outline",
                    "section": "discovery",
                    "permission": "discovery",
                    "order": 90,
                }
            ]

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

        def run_scheduler_once(self) -> dict[str, Any]:
            if not self._enabled:
                return {"reason": "plugin_disabled"}
            if not self._storage_bootstrapped:
                _bootstrap_plugin_storage()
                self._storage_bootstrapped = True
            scheduler_module = _load_local_module("startup.scheduler")
            return scheduler_module.run_subscription_scheduler_once()

        def run_chart_refresh_once(self) -> dict[str, Any]:
            if not self._enabled:
                return {"reason": "plugin_disabled"}
            if not self._storage_bootstrapped:
                _bootstrap_plugin_storage()
                self._storage_bootstrapped = True
            scheduler_module = _load_local_module("startup.scheduler")
            return scheduler_module.run_chart_refresh_once()

        def run_transfer_once(self) -> dict[str, Any]:
            if not self._enabled:
                return {"reason": "plugin_disabled"}
            if not self._storage_bootstrapped:
                _bootstrap_plugin_storage()
                self._storage_bootstrapped = True
            scheduler_module = _load_local_module("startup.scheduler")
            return scheduler_module.run_transfer_once()

        def stop_service(self):
            return None
