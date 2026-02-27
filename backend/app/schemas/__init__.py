"""
Schemas 包
导出所有 Schema 模型
"""

from app.schemas.types import (
    EventType,
    DownloadStatus,
    MediaType,
    PlaylistType,
    DownloaderType,
    MediaServerType,
    MessageChannel,
    NotificationType,
)

from app.schemas.response import (
    ResponseModel,
    PaginatedResponse,
    ErrorResponse,
    ValidationErrorResponse,
    ValidationErrorDetail,
)

from app.schemas.artist import (
    ArtistBase,
    ArtistCreate,
    ArtistUpdate,
    ArtistResponse,
    ArtistListResponse,
)

from app.schemas.album import (
    AlbumBase,
    AlbumCreate,
    AlbumUpdate,
    AlbumResponse,
    AlbumListResponse,
)

from app.schemas.track import (
    TrackBase,
    TrackCreate,
    TrackUpdate,
    TrackResponse,
    TrackListResponse,
    TrackStreamInfo,
)

from app.schemas.playlist import (
    PlaylistBase,
    PlaylistCreate,
    PlaylistUpdate,
    PlaylistResponse,
    PlaylistTrackBase,
    PlaylistTrackResponse,
    PlaylistWithTracksResponse,
    PlaylistListResponse,
    AddTrackRequest,
    BatchAddTracksRequest,
    ReorderTracksRequest,
)

from app.schemas.library import (
    LibraryBase,
    LibraryCreate,
    LibraryUpdate,
    LibraryResponse,
    LibraryListResponse,
    ScanLibraryRequest,
)

from app.schemas.download import (
    DownloadBase,
    DownloadRequest,
    DownloadHistoryBase,
    DownloadHistoryResponse,
    DownloadHistoryListResponse,
    DownloadProgress,
    RetryDownloadRequest,
)

from app.schemas.subscribe import (
    SubscribeBase,
    SubscribeCreate,
    SubscribeUpdate,
    SubscribeResponse,
    SubscribeListResponse,
    CheckSubscribeResponse,
)

from app.schemas.site import (
    SiteBase,
    SiteCreate,
    SiteUpdate,
    SiteResponse,
    SiteListResponse,
    TestSiteRequest,
    TestSiteResponse,
)

from app.schemas.subscribe_release import (
    SubscribeReleaseBase,
    SubscribeReleaseCreate,
    SubscribeReleaseUpdate,
    SubscribeReleaseResponse,
    SubscribeReleaseListResponse,
    SubscribeReleaseStatistics,
)

from app.schemas.media import (
    MediaServerBase,
    MediaServerCreate,
    MediaServerUpdate,
    MediaServerResponse,
    MediaServerListResponse,
    MediaServerStatus,
    ScanMediaServerRequest,
)

from app.schemas.system import (
    SystemConfigBase,
    SystemConfigCreate,
    SystemConfigUpdate,
    SystemConfigResponse,
    SystemStats,
    SystemHealth,
    ScanAllRequest,
    LogEntry,
    LogsResponse,
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
