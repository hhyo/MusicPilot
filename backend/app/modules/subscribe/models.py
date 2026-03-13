"""
订阅模型 - 榜单订阅扩展
定义订阅类型和榜单数据源枚举
"""

import enum


class SubscriptionType(enum.StrEnum):
    """订阅类型"""

    ARTIST = "artist"
    ALBUM = "album"
    SINGLE = "single"
    PLAYLIST = "playlist"
    CHART = "chart"  # 🆕 新增榜单订阅类型


class ChartSource(enum.StrEnum):
    """榜单数据源 🆕 新增"""

    SPOTIFY = "spotify"
    APPLE_MUSIC = "apple_music"
    NETEASE = "netease"
    QQ_MUSIC = "qq_music"
    MTEAM = "mteam"
    OPENCD = "opencd"


# 重新导出 app.db.models.subscribe.Subscribe 以便统一使用
from app.db.models.subscribe import Subscribe as Subscription  # noqa: E402, F401

__all__ = [
    "SubscriptionType",
    "ChartSource",
    "Subscription",
]
