"""Metadata module for metadata search and detail routes."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.db import SessionLocal, initialize_database_schema
from ..db.acquisition_oper import AcquisitionOper
from ..db.metadata_oper import MetadataOper
from ..db.models.metadata import AlbumModel, ArtistModel, TrackModel
from ..db.orchestration_oper import OrchestrationOper
from ..modules.metadata_provider import MetadataProviderAdapter, MockMetadataProviderAdapter
from ..schemas.metadata import MetadataDetail, MetadataReference, MetadataSearchData, MetadataSearchRequest, MetadataSummary
from ..schemas.shared import EntityType, ReleaseType


INTEGRATION_POINT = "Local metadata repository backed by the current provider mode."


@dataclass(slots=True)
class MetadataBootstrapSummary:
    database_url: str
    provider: str
    source_type: str
    seeded: bool
    counts: dict[str, int]


class MetadataModule:
    def __init__(self, session: Session, provider: MetadataProviderAdapter):
        self.session = session
        self.provider = provider
        self.oper = MetadataOper(session)

    def search(self, payload: MetadataSearchRequest) -> MetadataSearchData:
        if self.provider.supports_live_queries:
            result = self.provider.search(payload)
            self.oper.record_search_history(
                keyword=payload.keyword,
                entity_type=payload.type.value,
                page=payload.page,
                page_size=payload.page_size,
                result_count=result.total,
                provider=result.provider,
                source_type=result.source_type,
            )
            self.session.commit()
            return result

        handlers = {
            EntityType.ARTIST: self.oper.search_artists,
            EntityType.ALBUM: self.oper.search_albums,
            EntityType.TRACK: self.oper.search_tracks,
        }
        items, total = handlers[payload.type](payload.keyword, payload.page, payload.page_size)
        summaries = [self._build_summary(item, payload.type) for item in items]
        self.oper.record_search_history(
            keyword=payload.keyword,
            entity_type=payload.type.value,
            page=payload.page,
            page_size=payload.page_size,
            result_count=total,
            provider=self.provider.provider,
            source_type=self.provider.source_type,
        )
        self.session.commit()
        return MetadataSearchData(
            keyword=payload.keyword,
            entity_type=payload.type,
            page=payload.page,
            page_size=payload.page_size,
            total=total,
            provider=self.provider.provider,
            source_type=self.provider.source_type,
            integration_point=INTEGRATION_POINT,
            items=summaries,
        )

    def get_detail(self, entity_type: EntityType, entity_id: str) -> MetadataDetail:
        if self.provider.supports_live_queries:
            return self.provider.get_detail(entity_type, entity_id)

        if entity_type == EntityType.ARTIST:
            artist = self.oper.get_artist(entity_id)
            if artist is None:
                raise HTTPException(status_code=404, detail=f"Artist {entity_id} was not found in the local seed catalog.")
            detail = self._build_summary(artist, EntityType.ARTIST)
            return MetadataDetail(
                **detail.model_dump(),
                country=artist.country,
                integration_point=INTEGRATION_POINT,
                related_albums=[MetadataReference(id=album.id, title=album.title, entity_type=EntityType.ALBUM, subtitle=album.artist_name) for album in artist.albums],
                tracks=[MetadataReference(id=track.id, title=track.title, entity_type=EntityType.TRACK, subtitle=track.album_title) for track in artist.tracks],
            )

        if entity_type == EntityType.ALBUM:
            album = self.oper.get_album(entity_id)
            if album is None:
                raise HTTPException(status_code=404, detail=f"Album {entity_id} was not found in the local seed catalog.")
            detail = self._build_summary(album, EntityType.ALBUM)
            return MetadataDetail(
                **detail.model_dump(),
                integration_point=INTEGRATION_POINT,
                related_artists=[MetadataReference(id=artist.id, title=artist.name, entity_type=EntityType.ARTIST, subtitle=artist.country) for artist in album.artists],
                tracks=[MetadataReference(id=track.id, title=track.title, entity_type=EntityType.TRACK, subtitle=track.artist_name) for track in album.tracks],
            )

        track = self.oper.get_track(entity_id)
        if track is None:
            raise HTTPException(status_code=404, detail=f"Track {entity_id} was not found in the local seed catalog.")
        detail = self._build_summary(track, EntityType.TRACK)
        related_album = None
        if track.album is not None:
            related_album = MetadataReference(id=track.album.id, title=track.album.title, entity_type=EntityType.ALBUM, subtitle=track.album.artist_name)
        return MetadataDetail(
            **detail.model_dump(),
            duration_seconds=track.duration_seconds,
            integration_point=INTEGRATION_POINT,
            related_artists=[MetadataReference(id=artist.id, title=artist.name, entity_type=EntityType.ARTIST, subtitle=artist.country) for artist in track.artists],
            related_album=related_album,
        )

    def get_detail_by_provider_ref(self, *, entity_type: EntityType, provider: str, provider_id: str) -> MetadataDetail:
        if provider != self.provider.provider:
            raise HTTPException(
                status_code=400,
                detail=f"Metadata provider ref '{provider}' does not match active metadata provider '{self.provider.provider}'.",
            )
        return self.get_detail(entity_type, provider_id)

    def _build_summary(self, item: ArtistModel | AlbumModel | TrackModel, entity_type: EntityType) -> MetadataSummary:
        if isinstance(item, ArtistModel):
            title = item.name
            artist_name = item.name
            album_title = None
            track_title = None
            release_type = None
            year = item.year
            note = item.note or f"Metadata loaded from {item.provider}."
        elif isinstance(item, AlbumModel):
            title = item.title
            artist_name = item.artist_name or ", ".join(artist.name for artist in item.artists)
            album_title = item.title
            track_title = None
            release_type = ReleaseType(item.release_type) if item.release_type else None
            year = item.year
            note = item.note or f"Metadata loaded from {item.provider}."
        else:
            title = item.title
            artist_name = item.artist_name or ", ".join(artist.name for artist in item.artists)
            album_title = item.album_title or (item.album.title if item.album else None)
            track_title = item.title
            release_type = ReleaseType(item.release_type) if item.release_type else None
            year = item.year
            note = item.note or f"Metadata loaded from {item.provider}."

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


def bootstrap_metadata_storage(*, reseed: bool = False, provider: MetadataProviderAdapter | None = None) -> MetadataBootstrapSummary:
    initialize_database_schema()
    resolved_provider = provider or MockMetadataProviderAdapter()

    seeded = False
    with SessionLocal() as session:
        metadata_oper = MetadataOper(session)
        acquisition_oper = AcquisitionOper(session)
        orchestration_oper = OrchestrationOper(session)
        if reseed:
            orchestration_oper.clear_all()
            acquisition_oper.clear_all()
            metadata_oper.clear_all()

        if settings.metadata_seed_enabled and not metadata_oper.has_seed_data():
            metadata_oper.seed_catalog(resolved_provider.load_seed_catalog())
            session.flush()
            seeded = True

        counts = metadata_oper.summary()
        session.commit()

    return MetadataBootstrapSummary(
        database_url=settings.database_url,
        provider=resolved_provider.provider,
        source_type=resolved_provider.source_type,
        seeded=seeded,
        counts=counts,
    )
