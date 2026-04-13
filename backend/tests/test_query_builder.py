"""Unit tests for the unified music-media query builder."""

from __future__ import annotations

import unittest

from app.schemas.acquisition import QueryPreferences
from app.schemas.metadata import MetadataDetail
from app.schemas.music_media import MusicMediaInfo
from app.schemas.shared import EntityType, ReleaseType
from app.services.query_builder import QueryBuilderService


def build_artist_media() -> MusicMediaInfo:
    return MusicMediaInfo(
        entity_type=EntityType.ARTIST,
        provider="musicbrainz",
        provider_id="artist-adele",
        title="Adele",
        artist_names=["Adele"],
        album_title=None,
        album_artist_names=[],
        year=2008,
        related_artist_ids=[],
        related_track_ids=[],
        external_refs={"musicbrainz_artist_id": "artist-adele"},
        match_evidence=[],
        diagnostics=[],
        release_context={},
        match_strategy="strong_ref",
    )


def build_album_media() -> MusicMediaInfo:
    return MusicMediaInfo(
        entity_type=EntityType.ALBUM,
        provider="musicbrainz",
        provider_id="release-group-25",
        title="25",
        artist_names=["Adele"],
        album_title="25",
        album_artist_names=["Adele"],
        year=2015,
        related_artist_ids=["artist-adele"],
        related_track_ids=[],
        external_refs={"musicbrainz_release_group_id": "release-group-25"},
        match_evidence=[],
        diagnostics=[],
        release_context={"aliases": ["二十五", "Twenty Five"]},
        match_strategy="strong_ref",
    )


def build_track_media() -> MusicMediaInfo:
    return MusicMediaInfo(
        entity_type=EntityType.TRACK,
        provider="musicbrainz",
        provider_id="recording-hello",
        title="Hello",
        artist_names=["Adele"],
        album_title="25",
        album_artist_names=["Adele"],
        year=2015,
        related_artist_ids=["artist-adele"],
        related_album_id="release-group-25",
        related_track_ids=[],
        external_refs={"musicbrainz_recording_id": "recording-hello"},
        match_evidence=[],
        diagnostics=[],
        release_context={"aliases": ["哈喽"]},
        match_strategy="strong_ref",
    )


def build_artist_detail() -> MetadataDetail:
    return MetadataDetail(
        entity_type=EntityType.ARTIST,
        id="artist-adele",
        title="Adele",
        artist_name="Adele",
        aliases=["阿黛尔", "Adele Laurie"],
        year=2008,
        genres=["Pop", "Soul"],
        external_ids={"musicbrainz": "artist-adele"},
        provider="musicbrainz",
        source_type="musicbrainz",
        mock=False,
        note="test",
        country="UK",
        integration_point="test",
    )


def build_album_detail() -> MetadataDetail:
    return MetadataDetail(
        entity_type=EntityType.ALBUM,
        id="release-group-25",
        title="25",
        artist_name="Adele",
        album_title="25",
        aliases=["二十五", "Twenty Five"],
        year=2015,
        release_type=ReleaseType.ALBUM,
        genres=["Pop", "Soul"],
        external_ids={"musicbrainz": "release-group-25"},
        provider="musicbrainz",
        source_type="musicbrainz",
        mock=False,
        note="test",
        integration_point="test",
    )


def build_track_detail() -> MetadataDetail:
    return MetadataDetail(
        entity_type=EntityType.TRACK,
        id="recording-hello",
        title="Hello",
        artist_name="Adele",
        album_title="25",
        track_title="Hello",
        aliases=["哈喽"],
        year=2015,
        release_type=ReleaseType.ALBUM,
        genres=["Pop", "Soul"],
        external_ids={"musicbrainz": "recording-hello"},
        provider="musicbrainz",
        source_type="musicbrainz",
        mock=False,
        note="test",
        integration_point="test",
    )


class QueryBuilderServiceTest(unittest.TestCase):
    def test_track_ordered_queries_prioritize_pt_release_shapes(self) -> None:
        result = QueryBuilderService.build_from_music_media_info(build_track_media())
        top_sources = [query.source for query in result.ordered_queries[:4]]
        self.assertEqual(
            top_sources,
            [
                "canonical_title",
                "canonical_album_release",
                "canonical_track_album",
                "relaxed_primary",
            ],
        )

    def test_album_ordered_queries_prioritize_release_title_before_aliases(self) -> None:
        result = QueryBuilderService.build_from_music_media_info(build_album_media())
        top_sources = [query.source for query in result.ordered_queries[:4]]
        self.assertEqual(
            top_sources,
            [
                "canonical_title",
                "canonical_year",
                "relaxed_primary",
                "relaxed_album_only",
            ],
        )

    def test_album_canonical_query_contains_artist_and_title(self) -> None:
        result = QueryBuilderService.build_from_music_media_info(build_album_media())
        first_query = result.canonical_queries[0].query
        self.assertIn("Adele", first_query)
        self.assertIn("25", first_query)

    def test_album_canonical_query_contains_year_by_default(self) -> None:
        result = QueryBuilderService.build_from_music_media_info(build_album_media())
        self.assertTrue(any("2015" in query.query for query in result.canonical_queries))

    def test_album_alias_queries_include_release_context_aliases(self) -> None:
        result = QueryBuilderService.build_from_music_media_info(build_album_media())
        alias_terms = [query.query for query in result.alias_queries]
        self.assertTrue(any("二十五" in query for query in alias_terms))

    def test_track_canonical_query_contains_album_context(self) -> None:
        result = QueryBuilderService.build_from_music_media_info(build_track_media())
        self.assertTrue(any("25" in query.query for query in result.canonical_queries))

    def test_track_relaxed_queries_include_track_only_variant(self) -> None:
        result = QueryBuilderService.build_from_music_media_info(build_track_media())
        self.assertTrue(any(query.source == "relaxed_track_only" for query in result.relaxed_queries))

    def test_artist_relaxed_queries_keep_artist_only_variant(self) -> None:
        result = QueryBuilderService.build_from_music_media_info(build_artist_media())
        self.assertTrue(any(query.source == "relaxed_artist_only" for query in result.relaxed_queries))

    def test_negative_queries_include_live_by_default(self) -> None:
        result = QueryBuilderService.build_from_music_media_info(build_album_media())
        negatives = [query.query for query in result.negative_queries]
        self.assertIn("live", negatives)

    def test_negative_queries_exclude_live_when_allowed(self) -> None:
        result = QueryBuilderService.build_from_music_media_info(
            build_album_media(),
            QueryPreferences(allow_live=True),
        )
        negatives = [query.query for query in result.negative_queries]
        self.assertNotIn("live", negatives)

    def test_negative_queries_include_custom_keywords(self) -> None:
        result = QueryBuilderService.build_from_music_media_info(
            build_album_media(),
            QueryPreferences(negative_keywords=["demo", "camrip"]),
        )
        negatives = [query.query for query in result.negative_queries]
        self.assertIn("demo", negatives)
        self.assertIn("camrip", negatives)

    def test_query_context_preserves_external_refs(self) -> None:
        result = QueryBuilderService.build_from_music_media_info(build_track_media())
        self.assertEqual(
            result.query_context.external_refs["musicbrainz_recording_id"],
            "recording-hello",
        )

    def test_query_preferences_are_embedded_in_result(self) -> None:
        preferences = QueryPreferences(preferred_formats=["FLAC", "APE"], allow_remaster=True)
        result = QueryBuilderService.build_from_music_media_info(build_album_media(), preferences)
        self.assertEqual(result.preferences.preferred_formats, ["FLAC", "APE"])
        self.assertTrue(result.preferences.allow_remaster)

    def test_query_builder_accepts_music_media_info_track_input(self) -> None:
        media = build_track_media()

        queries = QueryBuilderService.build_queries_from_music_media_info(media)

        self.assertEqual(
            queries[:3],
            [
                "Adele Hello FLAC",
                "Adele 25 FLAC",
                "Adele Hello 25 FLAC",
            ],
        )

    def test_query_result_exposes_execution_plan_for_host_search(self) -> None:
        result = QueryBuilderService.build_from_music_media_info(build_track_media())

        self.assertTrue(result.search_ready)
        self.assertEqual(result.execution_plan.positive_query_count, len(result.ordered_queries))
        self.assertEqual(result.execution_plan.top_positive_queries[:3], [query.query for query in result.ordered_queries[:3]])
        self.assertIn("live", result.execution_plan.negative_terms)


if __name__ == "__main__":
    unittest.main()
