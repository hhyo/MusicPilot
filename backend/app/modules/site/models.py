"""Site Module 模型"""

from dataclasses import dataclass


@dataclass
class SiteConfig:
    """站点配置"""

    name: str
    url: str
    api_key: str | None = None
    cookie: str | None = None
    username: str | None = None
    password: str | None = None
    enabled: bool = True


@dataclass
class TorrentInfo:
    """种子信息"""

    id: str
    name: str
    site: str
    size: int
    seeders: int
    leechers: int
    download_url: str
    description: str | None = None
    files: list[str] | None = None


@dataclass
class TorrentDetail:
    """种子详情"""

    id: str
    name: str
    size: int
    description: str
    files: list[str]
    seeders: int
    leechers: int
