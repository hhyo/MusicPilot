"""Application settings for the MusicPilot backend skeleton."""

from __future__ import annotations

from pathlib import Path

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = BACKEND_ROOT / "data" / "musicpilot.db"


class Settings(BaseSettings):
    app_name: str = Field(default="MusicPilot Backend")
    api_prefix: str = Field(default="/api/v1/plugin/musicpilot")
    debug: bool = Field(default=False)
    allowed_origins: list[str] = Field(default_factory=lambda: ["*"])
    database_url: str = Field(default=f"sqlite:///{DEFAULT_DATABASE_PATH}")
    metadata_seed_enabled: bool = Field(default=True)
    host_integration_enabled: bool = Field(default=False)
    host_base_url: str | None = Field(default=None)
    host_auth_token: str | None = Field(default=None)
    host_timeout_seconds: float = Field(default=8.0, ge=0.5, le=60.0)
    host_verify_tls: bool = Field(default=True)
    host_verification_state: str = Field(default="placeholder")
    host_health_path: str | None = Field(default=None)
    host_sites_path: str | None = Field(default=None)
    host_search_path: str | None = Field(default=None)
    host_downloaders_path: str | None = Field(default=None)
    host_dispatch_path: str | None = Field(default=None)
    host_organize_preview_path: str | None = Field(default=None)
    host_organize_apply_path: str | None = Field(default=None)
    host_notify_path: str | None = Field(default=None)
    host_config_path: str | None = Field(default=None)
    host_search_strategy: str = Field(default="mock")
    host_dispatch_strategy: str = Field(default="mock")
    host_organize_strategy: str = Field(default="mock")
    host_fallback_to_mock: bool = Field(default=True)
    host_strict_empty_as_error: bool = Field(default=False)
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
