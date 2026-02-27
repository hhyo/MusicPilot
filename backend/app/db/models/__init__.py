"""
数据库模型包
"""

from app.db.models.album import Album
from app.db.models.artist import Artist
from app.db.models.download import DownloadHistory
from app.db.models.library import Library
from app.db.models.media import MediaServer
from app.db.models.playlist import Playlist, PlaylistTrack
from app.db.models.site import Site
from app.db.models.subscribe import Subscribe
from app.db.models.subscribe_release import SubscribeRelease
from app.db.models.system import SystemConfig
from app.db.models.track import Track

__all__ = [
    "Artist",
    "Album",
    "Track",
    "Playlist",
    "PlaylistTrack",
    "Library",
    "DownloadHistory",
    "Subscribe",
    "Site",
    "SubscribeRelease",
    "MediaServer",
    "SystemConfig",
]
