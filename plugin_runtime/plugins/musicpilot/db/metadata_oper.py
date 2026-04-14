"""Metadata data access."""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session, selectinload

from .models.metadata import (
    AlbumModel,
    ArtistModel,
    SearchHistoryModel,
    TrackModel,
    album_artists,
    track_artists,
)
from ..schemas.metadata import MetadataSeedCatalog

ModelType = TypeVar("ModelType", ArtistModel, AlbumModel, TrackModel)


def build_search_text(*parts: str | None, values: list[str] | None = None) -> str:
    tokens = [part.strip().lower() for part in parts if part and part.strip()]
    if values:
        tokens.extend(value.strip().lower() for value in values if value and value.strip())
    return " ".join(dict.fromkeys(tokens))


class MetadataOper:
    def __init__(self, session: Session):
        self.session = session

    def has_seed_data(self) -> bool:
        return bool(self.session.scalar(select(func.count(ArtistModel.id))))

    def clear_all(self) -> None:
        self.session.execute(delete(track_artists))
        self.session.execute(delete(album_artists))
        self.session.execute(delete(SearchHistoryModel))
        self.session.execute(delete(TrackModel))
        self.session.execute(delete(AlbumModel))
        self.session.execute(delete(ArtistModel))

    def seed_catalog(self, catalog: MetadataSeedCatalog) -> None:
        artist_map: dict[str, ArtistModel] = {}
        album_map: dict[str, AlbumModel] = {}

        for artist in catalog.artists:
            artist_model = ArtistModel(
                id=artist.id,
                provider=catalog.provider,
                source_type=catalog.source_type,
                name=artist.name,
                aliases=artist.aliases,
                genres=artist.genres,
                external_ids=artist.external_ids,
                metadata_json=artist.metadata_json,
                search_text=build_search_text(artist.name, values=artist.aliases + artist.genres),
                country=artist.country,
                year=artist.year,
                note=artist.note or catalog.note,
            )
            artist_map[artist.id] = artist_model
            self.session.add(artist_model)

        for album in catalog.albums:
            album_model = AlbumModel(
                id=album.id,
                provider=catalog.provider,
                source_type=catalog.source_type,
                title=album.title,
                artist_name=album.artist_name,
                aliases=album.aliases,
                year=album.year,
                release_type=album.release_type.value if album.release_type else None,
                genres=album.genres,
                external_ids=album.external_ids,
                metadata_json=album.metadata_json,
                search_text=build_search_text(
                    album.title,
                    album.artist_name,
                    values=album.aliases + album.genres,
                ),
                note=album.note or catalog.note,
            )
            album_model.artists = [artist_map[artist_id] for artist_id in album.artist_ids if artist_id in artist_map]
            album_map[album.id] = album_model
            self.session.add(album_model)

        for track in catalog.tracks:
            track_model = TrackModel(
                id=track.id,
                provider=catalog.provider,
                source_type=catalog.source_type,
                title=track.title,
                artist_name=track.artist_name,
                album_title=track.album_title,
                aliases=track.aliases,
                year=track.year,
                version=track.version,
                release_type=track.release_type.value if track.release_type else None,
                genres=track.genres,
                external_ids=track.external_ids,
                metadata_json=track.metadata_json,
                search_text=build_search_text(
                    track.title,
                    track.artist_name,
                    track.album_title,
                    values=track.aliases + track.genres,
                ),
                duration_seconds=track.duration_seconds,
                album=album_map.get(track.album_id) if track.album_id else None,
                note=track.note or catalog.note,
            )
            track_model.artists = [artist_map[artist_id] for artist_id in track.artist_ids if artist_id in artist_map]
            self.session.add(track_model)

    def record_search_history(
        self,
        *,
        keyword: str,
        entity_type: str,
        page: int,
        page_size: int,
        result_count: int,
        provider: str,
        source_type: str,
    ) -> None:
        self.session.add(
            SearchHistoryModel(
                keyword=keyword,
                entity_type=entity_type,
                page=page,
                page_size=page_size,
                result_count=result_count,
                provider=provider,
                source_type=source_type,
            )
        )

    def search_artists(self, keyword: str, page: int, page_size: int) -> tuple[list[ArtistModel], int]:
        return self._search_models(ArtistModel, keyword, page, page_size, ArtistModel.name)

    def search_albums(self, keyword: str, page: int, page_size: int) -> tuple[list[AlbumModel], int]:
        statement = (
            select(AlbumModel)
            .options(selectinload(AlbumModel.artists))
            .where(self._keyword_filter(AlbumModel, keyword))
            .order_by(func.coalesce(AlbumModel.year, 0).desc(), AlbumModel.title.asc())
        )
        return self._paginate(statement, page, page_size)

    def search_tracks(self, keyword: str, page: int, page_size: int) -> tuple[list[TrackModel], int]:
        statement = (
            select(TrackModel)
            .options(selectinload(TrackModel.artists), selectinload(TrackModel.album))
            .where(self._keyword_filter(TrackModel, keyword))
            .order_by(func.coalesce(TrackModel.year, 0).desc(), TrackModel.title.asc())
        )
        return self._paginate(statement, page, page_size)

    def get_artist(self, artist_id: str) -> ArtistModel | None:
        statement = (
            select(ArtistModel)
            .options(selectinload(ArtistModel.albums), selectinload(ArtistModel.tracks))
            .where(ArtistModel.id == artist_id)
        )
        return self.session.scalar(statement)

    def get_album(self, album_id: str) -> AlbumModel | None:
        statement = (
            select(AlbumModel)
            .options(selectinload(AlbumModel.artists), selectinload(AlbumModel.tracks))
            .where(AlbumModel.id == album_id)
        )
        return self.session.scalar(statement)

    def get_track(self, track_id: str) -> TrackModel | None:
        statement = (
            select(TrackModel)
            .options(selectinload(TrackModel.artists), selectinload(TrackModel.album))
            .where(TrackModel.id == track_id)
        )
        return self.session.scalar(statement)

    def summary(self) -> dict[str, int]:
        return {
            "artists": int(self.session.scalar(select(func.count(ArtistModel.id))) or 0),
            "albums": int(self.session.scalar(select(func.count(AlbumModel.id))) or 0),
            "tracks": int(self.session.scalar(select(func.count(TrackModel.id))) or 0),
            "search_history": int(self.session.scalar(select(func.count(SearchHistoryModel.id))) or 0),
        }

    def _keyword_filter(self, model: type[ModelType], keyword: str):
        needle = f"%{keyword.strip().lower()}%"
        return or_(
            func.lower(model.search_text).like(needle),
        )

    def _search_models(
        self,
        model: type[ModelType],
        keyword: str,
        page: int,
        page_size: int,
        order_column,
    ) -> tuple[list[ModelType], int]:
        statement = select(model).where(self._keyword_filter(model, keyword)).order_by(order_column.asc())
        return self._paginate(statement, page, page_size)

    def _paginate(self, statement, page: int, page_size: int):
        count_statement = select(func.count()).select_from(statement.order_by(None).subquery())
        total = int(self.session.scalar(count_statement) or 0)
        items = self.session.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
        return list(items), total
