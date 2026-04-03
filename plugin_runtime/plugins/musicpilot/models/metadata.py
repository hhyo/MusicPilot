"""Minimal metadata persistence models for Phase 2."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


album_artists = Table(
    "album_artists",
    Base.metadata,
    Column("album_id", ForeignKey("albums.id"), primary_key=True),
    Column("artist_id", ForeignKey("artists.id"), primary_key=True),
)


track_artists = Table(
    "track_artists",
    Base.metadata,
    Column("track_id", ForeignKey("tracks.id"), primary_key=True),
    Column("artist_id", ForeignKey("artists.id"), primary_key=True),
)


class ArtistModel(Base):
    __tablename__ = "artists"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), index=True)
    source_type: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    aliases: Mapped[list[str]] = mapped_column(JSON, default=list)
    genres: Mapped[list[str]] = mapped_column(JSON, default=list)
    external_ids: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    search_text: Mapped[str] = mapped_column(Text, index=True)
    country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    albums: Mapped[list["AlbumModel"]] = relationship(
        secondary=album_artists,
        back_populates="artists",
    )
    tracks: Mapped[list["TrackModel"]] = relationship(
        secondary=track_artists,
        back_populates="artists",
    )


class AlbumModel(Base):
    __tablename__ = "albums"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), index=True)
    source_type: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    artist_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    aliases: Mapped[list[str]] = mapped_column(JSON, default=list)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    release_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    genres: Mapped[list[str]] = mapped_column(JSON, default=list)
    external_ids: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    search_text: Mapped[str] = mapped_column(Text, index=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    artists: Mapped[list[ArtistModel]] = relationship(
        secondary=album_artists,
        back_populates="albums",
    )
    tracks: Mapped[list["TrackModel"]] = relationship(back_populates="album")


class TrackModel(Base):
    __tablename__ = "tracks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), index=True)
    source_type: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    artist_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    album_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    aliases: Mapped[list[str]] = mapped_column(JSON, default=list)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    release_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    genres: Mapped[list[str]] = mapped_column(JSON, default=list)
    external_ids: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    search_text: Mapped[str] = mapped_column(Text, index=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    album_id: Mapped[str | None] = mapped_column(ForeignKey("albums.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    album: Mapped[AlbumModel | None] = relationship(back_populates="tracks")
    artists: Mapped[list[ArtistModel]] = relationship(
        secondary=track_artists,
        back_populates="tracks",
    )


class SearchHistoryModel(Base):
    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keyword: Mapped[str] = mapped_column(String(255), index=True)
    entity_type: Mapped[str] = mapped_column(String(32), index=True)
    page: Mapped[int] = mapped_column(Integer, default=1)
    page_size: Mapped[int] = mapped_column(Integer, default=20)
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    provider: Mapped[str] = mapped_column(String(64))
    source_type: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
