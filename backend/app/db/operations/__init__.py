"""
数据库操作类包
"""
from app.db.operations.artist import ArtistOper
from app.db.operations.album import AlbumOper
from app.db.operations.track import TrackOper
from app.db.operations.playlist import PlaylistOper
from app.db.operations.library import LibraryOper
from app.db.operations.download import DownloadHistoryOper
from app.db.operations.subscribe import SubscribeOper
from app.db.operations.site import SiteOper
from app.db.operations.subscribe_release import SubscribeReleaseOper
from app.db.operations.media import MediaServerOper
from app.db.operations.system import SystemConfigOper

__all__ = [
    "ArtistOper",
    "AlbumOper",
    "TrackOper",
    "PlaylistOper",
    "LibraryOper",
    "DownloadHistoryOper",
    "SubscribeOper",
    "SiteOper",
    "SubscribeReleaseOper",
    "MediaServerOper",
    "SystemConfigOper",
]