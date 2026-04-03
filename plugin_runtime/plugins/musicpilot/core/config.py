"""Application settings for the MusicPilot backend skeleton."""

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
