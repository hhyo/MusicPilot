"""
Schemas 包
导出所有 Schema 模型
"""

from app.schemas.album import (
    AlbumBase,
    AlbumCreate,
    AlbumListResponse,
    AlbumResponse,
    AlbumUpdate,
)
from app.schemas.artist import (
    ArtistBase,
    ArtistCreate,
    ArtistListResponse,
    ArtistResponse,
    ArtistUpdate,
)
from app.schemas.download import (
    DownloadBase,
    DownloadHistoryBase,
    DownloadHistoryListResponse,
    DownloadHistoryResponse,
    DownloadProgress,
    DownloadRequest,
    RetryDownloadRequest,
)
from app.schemas.library import (
    LibraryBase,
    LibraryCreate,
    LibraryListResponse,
    LibraryResponse,
    LibraryUpdate,
    ScanLibraryRequest,
)
from app.schemas.media import (
    MediaServerBase,
    MediaServerCreate,
    MediaServerListResponse,
    MediaServerResponse,
    MediaServerStatus,
    MediaServerUpdate,
    ScanMediaServerRequest,
)
from app.schemas.playlist import (
    AddTrackRequest,
    BatchAddTracksRequest,
    PlaylistBase,
    PlaylistCreate,
    PlaylistListResponse,
    PlaylistResponse,
    PlaylistTrackBase,
    PlaylistTrackResponse,
    PlaylistUpdate,
    PlaylistWithTracksResponse,
    ReorderTracksRequest,
)
from app.schemas.response import (
    ErrorResponse,
    PaginatedResponse,
    ResponseModel,
    ValidationErrorDetail,
    ValidationErrorResponse,
)
from app.schemas.site import (
    SiteBase,
    SiteCreate,
    SiteListResponse,
    SiteResponse,
    SiteUpdate,
    TestSiteRequest,
    TestSiteResponse,
)
from app.schemas.subscribe import (
    CheckSubscribeResponse,
    SubscribeBase,
    SubscribeCreate,
    SubscribeListResponse,
    SubscribeResponse,
    SubscribeUpdate,
)
from app.schemas.subscribe_release import (
    SubscribeReleaseBase,
    SubscribeReleaseCreate,
    SubscribeReleaseListResponse,
    SubscribeReleaseResponse,
    SubscribeReleaseStatistics,
    SubscribeReleaseUpdate,
)
from app.schemas.system import (
    LogEntry,
    LogsResponse,
    ScanAllRequest,
    SystemConfigBase,
    SystemConfigCreate,
    SystemConfigResponse,
    SystemConfigUpdate,
    SystemHealth,
    SystemStats,
)
from app.schemas.track import (
    TrackBase,
    TrackCreate,
    TrackListResponse,
    TrackResponse,
    TrackStreamInfo,
    TrackUpdate,
)
from app.schemas.types import (
    DownloaderType,
    DownloadStatus,
    EventType,
    MediaServerType,
    MediaType,
    MessageChannel,
    NotificationType,
    PlaylistType,
)

__all__ = [
    # Types
    "EventType",
    "DownloadStatus",
    "MediaType",
    "PlaylistType",
    "DownloaderType",
    "MediaServerType",
    "MessageChannel",
    "NotificationType",
    # Response
    "ResponseModel",
    "PaginatedResponse",
    "ErrorResponse",
    "ValidationErrorResponse",
    "ValidationErrorDetail",
    # Artist
    "ArtistBase",
    "ArtistCreate",
    "ArtistUpdate",
    "ArtistResponse",
    "ArtistListResponse",
    # Album
    "AlbumBase",
    "AlbumCreate",
    "AlbumUpdate",
    "AlbumResponse",
    "AlbumListResponse",
    # Track
    "TrackBase",
    "TrackCreate",
    "TrackUpdate",
    "TrackResponse",
    "TrackListResponse",
    "TrackStreamInfo",
    # Playlist
    "PlaylistBase",
    "PlaylistCreate",
    "PlaylistUpdate",
    "PlaylistResponse",
    "PlaylistTrackBase",
    "PlaylistTrackResponse",
    "PlaylistWithTracksResponse",
    "PlaylistListResponse",
    "AddTrackRequest",
    "BatchAddTracksRequest",
    "ReorderTracksRequest",
    # Library
    "LibraryBase",
    "LibraryCreate",
    "LibraryUpdate",
    "LibraryResponse",
    "LibraryListResponse",
    "ScanLibraryRequest",
    # Download
    "DownloadBase",
    "DownloadRequest",
    "DownloadHistoryBase",
    "DownloadHistoryResponse",
    "DownloadHistoryListResponse",
    "DownloadProgress",
    "RetryDownloadRequest",
    # Subscribe
    "SubscribeBase",
    "SubscribeCreate",
    "SubscribeUpdate",
    "SubscribeResponse",
    "SubscribeListResponse",
    "CheckSubscribeResponse",
    # Site
    "SiteBase",
    "SiteCreate",
    "SiteUpdate",
    "SiteResponse",
    "SiteListResponse",
    "TestSiteRequest",
    "TestSiteResponse",
    # SubscribeRelease
    "SubscribeReleaseBase",
    "SubscribeReleaseCreate",
    "SubscribeReleaseUpdate",
    "SubscribeReleaseResponse",
    "SubscribeReleaseListResponse",
    "SubscribeReleaseStatistics",
    # Media
    "MediaServerBase",
    "MediaServerCreate",
    "MediaServerUpdate",
    "MediaServerResponse",
    "MediaServerListResponse",
    "MediaServerStatus",
    "ScanMediaServerRequest",
    # System
    "SystemConfigBase",
    "SystemConfigCreate",
    "SystemConfigUpdate",
    "SystemConfigResponse",
    "SystemStats",
    "SystemHealth",
    "ScanAllRequest",
    "LogEntry",
    "LogsResponse",
]
