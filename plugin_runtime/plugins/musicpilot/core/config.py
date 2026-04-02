"""Application settings for the MusicPilot backend skeleton."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="MusicPilot Backend")
    api_prefix: str = Field(default="/api/v1/plugin/musicpilot")
    debug: bool = Field(default=False)
    allowed_origins: list[str] = Field(default_factory=lambda: ["*"])

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

