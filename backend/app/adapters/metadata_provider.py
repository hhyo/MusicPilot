"""Adapter boundary for metadata providers used in Phase 2."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..schemas.metadata import MetadataSeedCatalog, SeedAlbum, SeedArtist, SeedTrack
from ..schemas.mvp import ReleaseType


class MetadataProviderAdapter(ABC):
    """Provider boundary for metadata ingestion."""

    @property
    @abstractmethod
    def provider(self) -> str:
        """Logical provider name."""

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Descriptor for source provenance."""

    @abstractmethod
    def load_seed_catalog(self) -> MetadataSeedCatalog:
        """Return the local seed catalog for the current stage."""


class MockMetadataProviderAdapter(MetadataProviderAdapter):
    """Local-seed metadata adapter for the Phase 2 minimum loop."""

    @property
    def provider(self) -> str:
        return "mock_seed_catalog"

    @property
    def source_type(self) -> str:
        return "local_seed"

    def load_seed_catalog(self) -> MetadataSeedCatalog:
        return MetadataSeedCatalog(
            provider=self.provider,
            source_type=self.source_type,
            note=(
                "当前元数据来自本地静态 seed，不代表已接入 QQ、网易云、Spotify、"
                "MusicBrainz 等外部音乐源。"
            ),
            artists=[
                SeedArtist(
                    id="artist-adele",
                    name="Adele",
                    aliases=["阿黛尔"],
                    genres=["Pop", "Soul"],
                    year=2008,
                    country="UK",
                    external_ids={"musicbrainz": "mock-mb-artist-adele"},
                    metadata_json={"query_builder_hint": "adele"},
                ),
                SeedArtist(
                    id="artist-taylor-swift",
                    name="Taylor Swift",
                    aliases=["泰勒·斯威夫特", "TS"],
                    genres=["Pop", "Country"],
                    year=2006,
                    country="US",
                    external_ids={"musicbrainz": "mock-mb-artist-taylor-swift"},
                    metadata_json={"query_builder_hint": "taylor swift"},
                ),
                SeedArtist(
                    id="artist-daft-punk",
                    name="Daft Punk",
                    aliases=["蠢朋克"],
                    genres=["Electronic", "Disco"],
                    year=1993,
                    country="FR",
                    external_ids={"musicbrainz": "mock-mb-artist-daft-punk"},
                    metadata_json={"query_builder_hint": "daft punk"},
                ),
                SeedArtist(
                    id="artist-billie-eilish",
                    name="Billie Eilish",
                    aliases=["比莉·艾利什"],
                    genres=["Pop", "Alternative"],
                    year=2016,
                    country="US",
                    external_ids={"musicbrainz": "mock-mb-artist-billie-eilish"},
                    metadata_json={"query_builder_hint": "billie eilish"},
                ),
            ],
            albums=[
                SeedAlbum(
                    id="album-25",
                    title="25",
                    artist_ids=["artist-adele"],
                    artist_name="Adele",
                    aliases=["二十五"],
                    year=2015,
                    release_type=ReleaseType.ALBUM,
                    genres=["Pop", "Soul"],
                    external_ids={"musicbrainz": "mock-mb-album-25"},
                ),
                SeedAlbum(
                    id="album-1989-tv",
                    title="1989 (Taylor's Version)",
                    artist_ids=["artist-taylor-swift"],
                    artist_name="Taylor Swift",
                    aliases=["1989 重录版"],
                    year=2023,
                    release_type=ReleaseType.ALBUM,
                    genres=["Pop"],
                    external_ids={"musicbrainz": "mock-mb-album-1989-tv"},
                ),
                SeedAlbum(
                    id="album-random-access-memories",
                    title="Random Access Memories",
                    artist_ids=["artist-daft-punk"],
                    artist_name="Daft Punk",
                    aliases=["随机存取的回忆"],
                    year=2013,
                    release_type=ReleaseType.ALBUM,
                    genres=["Electronic", "Disco"],
                    external_ids={"musicbrainz": "mock-mb-album-ram"},
                ),
                SeedAlbum(
                    id="album-hit-me-hard-and-soft",
                    title="Hit Me Hard and Soft",
                    artist_ids=["artist-billie-eilish"],
                    artist_name="Billie Eilish",
                    year=2024,
                    release_type=ReleaseType.ALBUM,
                    genres=["Pop", "Alternative"],
                    external_ids={"musicbrainz": "mock-mb-album-hit-me-hard-and-soft"},
                ),
            ],
            tracks=[
                SeedTrack(
                    id="track-hello",
                    title="Hello",
                    artist_ids=["artist-adele"],
                    artist_name="Adele",
                    album_id="album-25",
                    album_title="25",
                    year=2015,
                    release_type=ReleaseType.ALBUM,
                    genres=["Pop", "Soul"],
                    external_ids={"musicbrainz": "mock-mb-track-hello"},
                    duration_seconds=295,
                ),
                SeedTrack(
                    id="track-anti-hero",
                    title="Anti-Hero",
                    artist_ids=["artist-taylor-swift"],
                    artist_name="Taylor Swift",
                    album_title="Midnights",
                    aliases=["反英雄"],
                    year=2022,
                    release_type=ReleaseType.ALBUM,
                    genres=["Pop"],
                    external_ids={"musicbrainz": "mock-mb-track-anti-hero"},
                    duration_seconds=201,
                ),
                SeedTrack(
                    id="track-get-lucky",
                    title="Get Lucky",
                    artist_ids=["artist-daft-punk"],
                    artist_name="Daft Punk",
                    album_id="album-random-access-memories",
                    album_title="Random Access Memories",
                    year=2013,
                    release_type=ReleaseType.ALBUM,
                    genres=["Electronic", "Disco"],
                    external_ids={"musicbrainz": "mock-mb-track-get-lucky"},
                    duration_seconds=369,
                ),
                SeedTrack(
                    id="track-birds-of-a-feather",
                    title="Birds of a Feather",
                    artist_ids=["artist-billie-eilish"],
                    artist_name="Billie Eilish",
                    album_id="album-hit-me-hard-and-soft",
                    album_title="Hit Me Hard and Soft",
                    year=2024,
                    release_type=ReleaseType.ALBUM,
                    genres=["Pop", "Alternative"],
                    external_ids={"musicbrainz": "mock-mb-track-birds-of-a-feather"},
                    duration_seconds=210,
                ),
            ],
        )
