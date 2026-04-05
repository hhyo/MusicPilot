"""Unit tests for the Phase 3 query builder."""

from __future__ import annotations

import unittest

from app.schemas.acquisition import QueryPreferences
from app.schemas.metadata import MetadataDetail
from app.schemas.mvp import EntityType, ReleaseType
from app.services.query_builder import QueryBuilderService


def build_artist_detail() -> MetadataDetail:
    return MetadataDetail(
        entity_type=EntityType.ARTIST,
        id="artist-adele",
        title="Adele",
        artist_name="Adele",
        aliases=["阿黛尔", "Adele Laurie"],
        year=2008,
        genres=["Pop", "Soul"],
        external_ids={"musicbrainz": "mock-artist-adele"},
        provider="mock_seed_catalog",
        source_type="local_seed",
        mock=True,
        note="mock",
        country="UK",
        integration_point="mock",
    )


def build_album_detail() -> MetadataDetail:
    return MetadataDetail(
        entity_type=EntityType.ALBUM,
        id="album-25",
        title="25",
        artist_name="Adele",
        album_title="25",
        aliases=["二十五", "Twenty Five"],
        year=2015,
        release_type=ReleaseType.ALBUM,
        genres=["Pop", "Soul"],
        external_ids={"musicbrainz": "mock-album-25"},
        provider="mock_seed_catalog",
        source_type="local_seed",
        mock=True,
        note="mock",
        integration_point="mock",
    )


def build_track_detail() -> MetadataDetail:
    return MetadataDetail(
        entity_type=EntityType.TRACK,
        id="track-hello",
        title="Hello",
        artist_name="Adele",
        album_title="25",
        track_title="Hello",
        aliases=["哈喽"],
        year=2015,
        release_type=ReleaseType.ALBUM,
        genres=["Pop", "Soul"],
        external_ids={"musicbrainz": "mock-track-hello"},
        provider="mock_seed_catalog",
        source_type="local_seed",
        mock=True,
        note="mock",
        integration_point="mock",
    )


class QueryBuilderServiceTest(unittest.TestCase):
    def test_track_ordered_queries_prioritize_pt_release_shapes(self) -> None:
        result = QueryBuilderService.build_from_detail(build_track_detail())
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
        result = QueryBuilderService.build_from_detail(build_album_detail())
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
        result = QueryBuilderService.build_from_detail(build_album_detail())
        first_query = result.canonical_queries[0].query
        self.assertIn("Adele", first_query)
        self.assertIn("25", first_query)

    def test_album_canonical_query_contains_year_by_default(self) -> None:
        result = QueryBuilderService.build_from_detail(build_album_detail())
        self.assertTrue(any("2015" in query.query for query in result.canonical_queries))

    def test_album_alias_queries_include_metadata_aliases(self) -> None:
        result = QueryBuilderService.build_from_detail(build_album_detail())
        alias_terms = [query.query for query in result.alias_queries]
        self.assertTrue(any("二十五" in query for query in alias_terms))

    def test_track_canonical_query_contains_album_context(self) -> None:
        result = QueryBuilderService.build_from_detail(build_track_detail())
        self.assertTrue(any("25" in query.query for query in result.canonical_queries))

    def test_track_relaxed_queries_include_track_only_variant(self) -> None:
        result = QueryBuilderService.build_from_detail(build_track_detail())
        self.assertTrue(any(query.source == "relaxed_track_only" for query in result.relaxed_queries))

    def test_artist_relaxed_queries_keep_artist_only_variant(self) -> None:
        result = QueryBuilderService.build_from_detail(build_artist_detail())
        self.assertTrue(any(query.source == "relaxed_artist_only" for query in result.relaxed_queries))

    def test_negative_queries_include_live_by_default(self) -> None:
        result = QueryBuilderService.build_from_detail(build_album_detail())
        negatives = [query.query for query in result.negative_queries]
        self.assertIn("live", negatives)

    def test_negative_queries_exclude_live_when_allowed(self) -> None:
        result = QueryBuilderService.build_from_detail(
            build_album_detail(),
            QueryPreferences(allow_live=True),
        )
        negatives = [query.query for query in result.negative_queries]
        self.assertNotIn("live", negatives)

    def test_negative_queries_include_custom_keywords(self) -> None:
        result = QueryBuilderService.build_from_detail(
            build_album_detail(),
            QueryPreferences(negative_keywords=["demo", "camrip"]),
        )
        negatives = [query.query for query in result.negative_queries]
        self.assertIn("demo", negatives)
        self.assertIn("camrip", negatives)

    def test_query_context_preserves_external_ids(self) -> None:
        result = QueryBuilderService.build_from_detail(build_track_detail())
        self.assertEqual(result.query_context.external_ids["musicbrainz"], "mock-track-hello")

    def test_query_preferences_are_embedded_in_result(self) -> None:
        preferences = QueryPreferences(preferred_formats=["FLAC", "APE"], allow_remaster=True)
        result = QueryBuilderService.build_from_detail(build_album_detail(), preferences)
        self.assertEqual(result.preferences.preferred_formats, ["FLAC", "APE"])
        self.assertTrue(result.preferences.allow_remaster)


if __name__ == "__main__":
    unittest.main()
