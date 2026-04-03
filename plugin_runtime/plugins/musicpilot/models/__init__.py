"""Domain model placeholders.

Phase 0 不提前实现 Artist / Album / Track / Subscription 等真实 ORM 模型。
"""
"""ORM model exports."""

from .base import Base
from .metadata import AlbumModel, ArtistModel, SearchHistoryModel, TrackModel

__all__ = [
    "AlbumModel",
    "ArtistModel",
    "Base",
    "SearchHistoryModel",
    "TrackModel",
]
