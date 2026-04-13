"""Application settings for the MusicPilot backend skeleton."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = BACKEND_ROOT / "data" / "musicpilot.db"
DEFAULT_CHART_RSS_FEEDS: list[dict[str, Any]] = [
    {
        "id": "netease-hot-tracks",
        "label": "网易云热歌榜",
        "url": "https://rsshub.rssforever.com/163/music/playlist/3778678",
        "category": "hot",
        "region": "CN",
        "enabled": True,
    },
    {
        "id": "netease-new-tracks",
        "label": "网易云新歌榜",
        "url": "https://rsshub.rssforever.com/163/music/playlist/3779629",
        "category": "new",
        "region": "CN",
        "enabled": True,
    },
    {
        "id": "netease-original-tracks",
        "label": "网易云原创榜",
        "url": "https://rsshub.rssforever.com/163/music/playlist/2884035",
        "category": "original",
        "region": "CN",
        "enabled": True,
    },
    {
        "id": "youtube-top-songs",
        "label": "YouTube 热门歌曲榜",
        "url": "https://rsshub.rssforever.com/youtube/charts/TopSongs",
        "category": "hot",
        "region": "Global",
        "enabled": True,
    },
    {
        "id": "youtube-top-artists",
        "label": "YouTube 热门歌手榜",
        "url": "https://rsshub.rssforever.com/youtube/charts/TopArtists",
        "category": "hot",
        "region": "Global",
        "enabled": True,
    },
]


def _is_plugin_runtime_module(module_name: str) -> bool:
    return module_name.startswith("app.plugins.musicpilot.")


def _load_host_settings_for_plugin_runtime(module_name: str) -> object | None:
    if not _is_plugin_runtime_module(module_name):
        return None
    try:
        from app.core.config import settings as host_settings
    except Exception:
        return None
    return host_settings


def _derive_plugin_runtime_host_defaults(*, module_name: str, host_settings: object | None) -> dict[str, object]:
    if not _is_plugin_runtime_module(module_name) or host_settings is None:
        return {}

    port = getattr(host_settings, "PORT", None)
    token = getattr(host_settings, "API_TOKEN", None)
    if not port or not token:
        return {}

    return {
        "host_integration_enabled": True,
        "host_base_url": f"http://127.0.0.1:{int(port)}",
        "host_auth_token": str(token),
        "host_auth_mode": "x_api_key",
        "host_api_key_header_name": "X-API-KEY",
        "host_search_mode": "prefer_host",
        "host_dispatch_mode": "prefer_host",
        "host_organize_mode": "prefer_host",
    }


PLUGIN_RUNTIME_HOST_DEFAULTS = _derive_plugin_runtime_host_defaults(
    module_name=__name__,
    host_settings=_load_host_settings_for_plugin_runtime(__name__),
)


def _plugin_runtime_default(key: str, fallback):
    return PLUGIN_RUNTIME_HOST_DEFAULTS.get(key, fallback)


class Settings(BaseSettings):
    app_name: str = Field(default="MusicPilot Backend")
    api_prefix: str = Field(default="/api/v1/plugin/musicpilot")
    debug: bool = Field(default=False)
    allowed_origins: list[str] = Field(default_factory=lambda: ["*"])
    database_url: str = Field(default=f"sqlite:///{DEFAULT_DATABASE_PATH}")
    metadata_seed_enabled: bool = Field(default=True)
    metadata_provider_mode: str = Field(default="seed")
    metadata_provider_timeout_seconds: float = Field(default=15.0, ge=1.0, le=60.0)
    metadata_musicbrainz_base_url: str = Field(default="https://musicbrainz.org/ws/2")
    metadata_provider_user_agent: str = Field(default="MusicPilot/0.1.0 (local)")
    metadata_cache_enabled: bool = Field(default=True)
    metadata_cache_maxsize: int = Field(default=512, ge=1, le=10000)
    metadata_search_cache_ttl_seconds: int = Field(default=1800, ge=1, le=86400)
    metadata_detail_cache_ttl_seconds: int = Field(default=21600, ge=1, le=604800)
    chart_provider_mode: str = Field(default="mock")
    chart_provider_timeout_seconds: float = Field(default=15.0, ge=1.0, le=60.0)
    chart_listenbrainz_base_url: str = Field(default="https://api.listenbrainz.org")
    chart_provider_user_agent: str = Field(default="MusicPilot/0.1.0 (local)")
    chart_listenbrainz_range: str = Field(default="week")
    chart_listenbrainz_count: int = Field(default=20, ge=1, le=100)
    chart_cache_enabled: bool = Field(default=True)
    chart_cache_maxsize: int = Field(default=256, ge=1, le=10000)
    chart_cache_ttl_seconds: int = Field(default=900, ge=1, le=86400)
    chart_refresh_enabled: bool = Field(default=True)
    chart_refresh_interval_minutes: int = Field(default=60, ge=1, le=10080)
    chart_rss_feeds: list[dict[str, Any]] = Field(
        default_factory=lambda: [dict(feed) for feed in DEFAULT_CHART_RSS_FEEDS]
    )
    subscription_scheduler_enabled: bool = Field(default=True)
    subscription_scheduler_poll_seconds: float = Field(default=30.0, ge=1.0, le=3600.0)
    subscription_scheduler_default_interval_minutes: int = Field(default=360, ge=1, le=10080)
    host_integration_enabled: bool = Field(default_factory=lambda: bool(_plugin_runtime_default("host_integration_enabled", False)))
    host_base_url: str | None = Field(default_factory=lambda: _plugin_runtime_default("host_base_url", None))
    host_auth_token: str | None = Field(default_factory=lambda: _plugin_runtime_default("host_auth_token", None))
    host_auth_mode: str = Field(default_factory=lambda: str(_plugin_runtime_default("host_auth_mode", "x_api_key")))
    host_api_key_header_name: str = Field(default_factory=lambda: str(_plugin_runtime_default("host_api_key_header_name", "X-API-KEY")))
    host_timeout_seconds: float = Field(default=20.0, ge=0.5, le=60.0)
    host_verify_tls: bool = Field(default=True)
    host_verification_state: str = Field(default="unverified")
    host_health_path: str | None = Field(default="/api/v1/search/last")
    host_sites_path: str | None = Field(default="/api/v1/site")
    host_search_title_path: str | None = Field(default="/api/v1/search/title")
    host_search_media_path: str | None = Field(default="/api/v1/search/media")
    host_search_last_path: str | None = Field(default="/api/v1/search/last")
    host_downloaders_path: str | None = Field(default="/api/v1/download/clients")
    host_download_add_path: str | None = Field(default="/api/v1/download/add")
    host_download_media_path: str | None = Field(default="/api/v1/download/")
    host_history_download_path: str | None = Field(default="/api/v1/history/download")
    host_history_transfer_path: str | None = Field(default="/api/v1/history/transfer")
    host_history_download_page_size: int = Field(default=500, ge=10, le=5000)
    host_history_download_max_pages: int = Field(default=20, ge=1, le=100)
    host_history_transfer_page_size: int = Field(default=200, ge=10, le=2000)
    host_history_transfer_max_pages: int = Field(default=10, ge=1, le=100)
    host_history_sync_retry_attempts: int = Field(default=3, ge=1, le=20)
    host_history_sync_retry_interval_seconds: float = Field(default=1.0, ge=0.0, le=30.0)
    host_handoff_pending_ttl_seconds: int = Field(default=120, ge=1, le=86400)
    host_transfer_name_path: str | None = Field(default="/api/v1/transfer/name")
    host_transfer_queue_path: str | None = Field(default="/api/v1/transfer/queue")
    host_transfer_manual_path: str | None = Field(default="/api/v1/transfer/manual")
    host_transfer_now_path: str | None = Field(default="/api/v1/transfer/now")
    host_notify_path: str | None = Field(default=None)
    host_config_path: str | None = Field(default=None)
    host_search_mode: str = Field(default_factory=lambda: str(_plugin_runtime_default("host_search_mode", "mock")))
    host_dispatch_mode: str = Field(default_factory=lambda: str(_plugin_runtime_default("host_dispatch_mode", "mock")))
    host_organize_mode: str = Field(default_factory=lambda: str(_plugin_runtime_default("host_organize_mode", "mock")))
    host_strict_empty_as_error: bool = Field(default=False)
    host_dispatch_validate_clients: bool = Field(default=True)
    host_assume_healthy: bool | None = Field(default=None)
    host_assume_search_available: bool | None = Field(default=None)
    host_assume_dispatch_available: bool | None = Field(default=None)
    host_assume_organize_available: bool | None = Field(default=None)
    host_assume_downloaders_available: bool | None = Field(default=None)
    host_assume_sites_visible: bool | None = Field(default=None)
    organize_library_type: str = Field(default="music")
    organize_root_path: str = Field(default="/library/musicpilot/library")
    organize_artist_dir_template: str = Field(default="{artist_name}")
    organize_album_dir_template: str = Field(default="{artist_name}/{year} - {album_title}")
    organize_track_file_template: str = Field(default="{track_title}.{format_ext}")
    organize_conflict_policy: str = Field(default="skip_existing")
    organize_transfer_type: str = Field(default="copy")
    host_validation_matrix_path: str = Field(
        default=str(BACKEND_ROOT / "data" / "host_validation_matrix.latest.json")
    )

    model_config = SettingsConfigDict(
        env_prefix="MUSICPILOT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
