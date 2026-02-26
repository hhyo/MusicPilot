"""
配置模块
基于 Pydantic Settings 的配置管理
"""
from typing import Optional, List
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    应用配置模型
    使用 Pydantic Settings 管理所有配置项
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )

    # 应用配置
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True

    # 数据库配置
    database_url: str = "postgresql+asyncpg://musicpilot:musicpilot@localhost:5432/musicpilot"
    database_echo: bool = False

    # Redis 配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # 日志配置
    log_level: str = "INFO"
    log_dir: str = "logs"

    # API 配置
    api_v1_prefix: str = "/api/v1"
    api_docs_enabled: bool = True

    # 缓存配置
    cache_dir: str = "cache"
    cache_ttl: int = 3600

    # 媒体目录配置
    media_dir: str = "/media/music"
    temp_dir: str = "/tmp/musicpilot"

    # MusicBrainz 配置
    musicbrainz_enabled: bool = True
    musicbrainz_app_name: str = "MusicPilot"
    musicbrainz_app_version: str = "0.1.0"

    # 订阅配置
    subscribe_enabled: bool = True
    subscribe_check_interval: int = 86400  # 24小时

    # 媒体服务器配置
    plex_enabled: bool = False
    jellyfin_enabled: bool = False

    @property
    def is_dev(self) -> bool:
        """是否为开发环境"""
        return self.app_env == "development"

    @property
    def is_prod(self) -> bool:
        """是否为生产环境"""
        return self.app_env == "production"

    @property
    def media_path(self) -> Path:
        """媒体目录路径"""
        return Path(self.media_dir)

    @property
    def temp_path(self) -> Path:
        """临时目录路径"""
        return Path(self.temp_dir)

    @property
    def cache_path(self) -> Path:
        """缓存目录路径"""
        return Path(self.cache_dir)

    @property
    def log_path(self) -> Path:
        """日志目录路径"""
        return Path(self.log_dir)

    def ensure_dirs(self):
        """确保必要的目录存在"""
        self.media_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.log_path.mkdir(parents=True, exist_ok=True)


# 全局配置实例
settings = Settings()