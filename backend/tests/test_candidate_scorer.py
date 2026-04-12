"""Unit tests for the unified music-media candidate scorer."""

from __future__ import annotations

import unittest

from app.adapters.host_search import normalize_title
from app.schemas.acquisition import HostSearchCandidate, QueryPreferences
from app.schemas.shared import DecisionStatus
from app.services.query_builder import QueryBuilderService
from app.services.scoring import MusicCandidateScorer
from tests.test_query_builder import build_album_media, build_track_media


class MusicCandidateScorerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.scorer = MusicCandidateScorer()

    def test_exact_lossless_candidate_is_auto_download(self) -> None:
        media = build_track_media()
        query_build = QueryBuilderService.build_from_music_media_info(media)
        candidate = HostSearchCandidate(
            site_id="mock-site-lossless",
            site_name="Mock Lossless",
            title="Adele - Hello [25] [FLAC]",
            normalized_title=normalize_title("Adele - Hello [25] [FLAC]"),
            size_bytes=2_000_000_000,
            seeders=30,
            peers=4,
            format_tag="flac",
            bitrate_kbps=1000,
            source_tags=["lossless"],
            note="mock",
        )
        score = self.scorer.score(
            media=media,
            query_build=query_build,
            candidate=candidate,
            preferences=QueryPreferences(),
        )
        self.assertEqual(score.decision, DecisionStatus.AUTO_DOWNLOAD)
        self.assertGreaterEqual(score.score_total, 90)

    def test_deluxe_aac_candidate_is_manual_confirm(self) -> None:
        media = build_album_media()
        query_build = QueryBuilderService.build_from_music_media_info(media)
        candidate = HostSearchCandidate(
            site_id="mock-site-scene",
            site_name="Mock Scene",
            title="Adele - 25 Deluxe Edition [AAC 320]",
            normalized_title=normalize_title("Adele - 25 Deluxe Edition [AAC 320]"),
            size_bytes=650_000_000,
            seeders=11,
            peers=6,
            format_tag="aac",
            bitrate_kbps=320,
            source_tags=["deluxe"],
            note="mock",
        )
        score = self.scorer.score(
            media=media,
            query_build=query_build,
            candidate=candidate,
            preferences=QueryPreferences(),
        )
        self.assertEqual(score.decision, DecisionStatus.MANUAL_CONFIRM)
        self.assertGreaterEqual(score.score_total, 70)

    def test_karaoke_candidate_is_rejected(self) -> None:
        media = build_track_media()
        query_build = QueryBuilderService.build_from_music_media_info(media)
        candidate = HostSearchCandidate(
            site_id="mock-site-noisy",
            site_name="Mock Noisy",
            title="Adele - Hello Karaoke Tribute [MP3 128]",
            normalized_title=normalize_title("Adele - Hello Karaoke Tribute [MP3 128]"),
            size_bytes=120_000_000,
            seeders=3,
            peers=8,
            format_tag="mp3",
            bitrate_kbps=128,
            source_tags=["karaoke", "tribute"],
            note="mock",
        )
        score = self.scorer.score(
            media=media,
            query_build=query_build,
            candidate=candidate,
            preferences=QueryPreferences(),
        )
        self.assertEqual(score.decision, DecisionStatus.REJECT)
        self.assertLess(score.score_total, 70)
        self.assertLess(score.score_breakdown["negative_keyword_penalty"].score, 0)

    def test_seeders_raise_score(self) -> None:
        media = build_album_media()
        query_build = QueryBuilderService.build_from_music_media_info(media)
        base_candidate = {
            "site_id": "mock-site",
            "site_name": "Mock Site",
            "title": "Adele - 25 Deluxe Edition [AAC 320]",
            "normalized_title": normalize_title("Adele - 25 Deluxe Edition [AAC 320]"),
            "size_bytes": 650_000_000,
            "format_tag": "aac",
            "bitrate_kbps": 320,
            "source_tags": ["deluxe"],
            "note": "mock",
        }
        high_seed = HostSearchCandidate(seeders=20, peers=4, **base_candidate)
        low_seed = HostSearchCandidate(seeders=1, peers=4, **base_candidate)

        high_score = self.scorer.score(
            media=media,
            query_build=query_build,
            candidate=high_seed,
            preferences=QueryPreferences(),
        )
        low_score = self.scorer.score(
            media=media,
            query_build=query_build,
            candidate=low_seed,
            preferences=QueryPreferences(),
        )
        self.assertGreater(high_score.score_total, low_score.score_total)


if __name__ == "__main__":
    unittest.main()
