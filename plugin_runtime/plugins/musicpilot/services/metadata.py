"""Metadata service for the Phase 2 minimum search loop."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..adapters.metadata_provider import MetadataProviderAdapter, MockMetadataProviderAdapter
from ..core.config import settings
from ..core.db import SessionLocal, initialize_database_schema
from ..models.metadata import AlbumModel, ArtistModel, TrackModel
from ..repositories.metadata import MetadataRepository
from ..schemas.metadata import (
    MetadataDetail,
    MetadataReference,
    MetadataSearchData,
    MetadataSearchRequest,
    MetadataSummary,
)
from ..schemas.mvp import EntityType, ReleaseType


INTEGRATION_POINT = "Replace MockMetadataProviderAdapter with a verified metadata provider adapter in a later phase."
DETAIL_TODO = [
    "Phase 2 仅提供 metadata 结果，不包含 PT 搜索、下载派发或整理结果。",
    "后续阶段可基于当前结构化字段构建 QueryBuilder 输入。",
]


@dataclass(slots=True)
class MetadataBootstrapSummary:
    database_url: str
    provider: str
    source_type: str
    seeded: bool
    counts: dict[str, int]


class MetadataService:
    def __init__(self, session: Session, adapter: MetadataProviderAdapter):
        self.session = session
        self.adapter = adapter
        self.repository = MetadataRepository(session)
        self.catalog_note = adapter.load_seed_catalog().note

    def search(self, payload: MetadataSearchRequest) -> MetadataSearchData:
        handlers = {
            EntityType.ARTIST: self.repository.search_artists,
            EntityType.ALBUM: self.repository.search_albums,
            EntityType.TRACK: self.repository.search_tracks,
        }
        items, total = handlers[payload.type](payload.keyword, payload.page, payload.page_size)
        summaries = [self._build_summary(item, payload.type) for item in items]
        self.repository.record_search_history(
            keyword=payload.keyword,
            entity_type=payload.type.value,
            page=payload.page,
            page_size=payload.page_size,
            result_count=total,
            provider=self.adapter.provider,
            source_type=self.adapter.source_type,
        )
        self.session.commit()
        return MetadataSearchData(
            keyword=payload.keyword,
            entity_type=payload.type,
            page=payload.page,
            page_size=payload.page_size,
            total=total,
            provider=self.adapter.provider,
            source_type=self.adapter.source_type,
            integration_point=INTEGRATION_POINT,
            items=summaries,
        )

    def get_artist_detail(self, artist_id: str) -> MetadataDetail:
        artist = self.repository.get_artist(artist_id)
        if artist is None:
            raise HTTPException(status_code=404, detail=f"Artist {artist_id} was not found in the local seed catalog.")
        detail = self._build_summary(artist, EntityType.ARTIST)
        return MetadataDetail(
            **detail.model_dump(),
            country=artist.country,
            integration_point=INTEGRATION_POINT,
            related_albums=[
                MetadataReference(
                    id=album.id,
                    title=album.title,
                    entity_type=EntityType.ALBUM,
                    subtitle=album.artist_name,
                )
                for album in artist.albums
            ],
            tracks=[
                MetadataReference(
                    id=track.id,
                    title=track.title,
                    entity_type=EntityType.TRACK,
                    subtitle=track.album_title,
                )
                for track in artist.tracks
            ],
            todo=DETAIL_TODO,
        )

    def get_album_detail(self, album_id: str) -> MetadataDetail:
        album = self.repository.get_album(album_id)
        if album is None:
            raise HTTPException(status_code=404, detail=f"Album {album_id} was not found in the local seed catalog.")
        detail = self._build_summary(album, EntityType.ALBUM)
        return MetadataDetail(
            **detail.model_dump(),
            integration_point=INTEGRATION_POINT,
            related_artists=[
                MetadataReference(
                    id=artist.id,
                    title=artist.name,
                    entity_type=EntityType.ARTIST,
                    subtitle=artist.country,
                )
                for artist in album.artists
            ],
            tracks=[
                MetadataReference(
                    id=track.id,
                    title=track.title,
                    entity_type=EntityType.TRACK,
                    subtitle=track.artist_name,
                )
                for track in album.tracks
            ],
            todo=DETAIL_TODO,
        )

    def get_track_detail(self, track_id: str) -> MetadataDetail:
        track = self.repository.get_track(track_id)
        if track is None:
            raise HTTPException(status_code=404, detail=f"Track {track_id} was not found in the local seed catalog.")
        detail = self._build_summary(track, EntityType.TRACK)
        related_album = None
        if track.album is not None:
            related_album = MetadataReference(
                id=track.album.id,
                title=track.album.title,
                entity_type=EntityType.ALBUM,
                subtitle=track.album.artist_name,
            )
        return MetadataDetail(
            **detail.model_dump(),
            duration_seconds=track.duration_seconds,
            integration_point=INTEGRATION_POINT,
            related_artists=[
                MetadataReference(
                    id=artist.id,
                    title=artist.name,
                    entity_type=EntityType.ARTIST,
                    subtitle=artist.country,
                )
                for artist in track.artists
            ],
            related_album=related_album,
            todo=DETAIL_TODO,
        )

    def _build_summary(
        self,
        item: ArtistModel | AlbumModel | TrackModel,
        entity_type: EntityType,
    ) -> MetadataSummary:
        if isinstance(item, ArtistModel):
            title = item.name
            artist_name = item.name
            album_title = None
            track_title = None
            release_type = None
            year = item.year
            note = item.note or self.catalog_note
        elif isinstance(item, AlbumModel):
            title = item.title
            artist_name = item.artist_name or ", ".join(artist.name for artist in item.artists)
            album_title = item.title
            track_title = None
            release_type = ReleaseType(item.release_type) if item.release_type else None
            year = item.year
            note = item.note or self.catalog_note
        else:
            title = item.title
            artist_name = item.artist_name or ", ".join(artist.name for artist in item.artists)
            album_title = item.album_title or (item.album.title if item.album else None)
            track_title = item.title
            release_type = ReleaseType(item.release_type) if item.release_type else None
            year = item.year
            note = item.note or self.catalog_note

        return MetadataSummary(
            entity_type=entity_type,
            id=item.id,
            title=title,
            artist_name=artist_name,
            album_title=album_title,
            track_title=track_title,
            aliases=list(item.aliases or []),
            year=year,
            release_type=release_type,
            genres=list(item.genres or []),
            external_ids=dict(item.external_ids or {}),
            provider=item.provider,
            source_type=item.source_type,
            mock=item.source_type in {"mock", "local_seed"},
            note=note,
        )


def bootstrap_metadata_storage(
    *,
    reseed: bool = False,
    adapter: MetadataProviderAdapter | None = None,
) -> MetadataBootstrapSummary:
    initialize_database_schema()

    resolved_adapter = adapter or MockMetadataProviderAdapter()
    seeded = False

    with SessionLocal() as session:
        repository = MetadataRepository(session)
        if reseed:
            repository.clear_all()

        if settings.metadata_seed_enabled and not repository.has_seed_data():
            repository.seed_catalog(resolved_adapter.load_seed_catalog())
            session.flush()
            seeded = True

        counts = repository.summary()
        session.commit()

    return MetadataBootstrapSummary(
        database_url=settings.database_url,
        provider=resolved_adapter.provider,
        source_type=resolved_adapter.source_type,
        seeded=seeded,
        counts=counts,
    )
