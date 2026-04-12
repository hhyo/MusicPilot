"""Candidate scoring rules for the Phase 3 minimum loop."""

from __future__ import annotations

import re

from ..schemas.acquisition import CandidateScoreResult, HostSearchCandidate, QueryBuildResult, QueryPreferences, ScoreBreakdownItem
from ..schemas.music_media import MusicMediaInfo
from ..schemas.shared import DecisionStatus, EntityType


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(TOKEN_PATTERN.findall(value.lower()))


def token_ratio(target: str, text: str) -> float:
    target_tokens = [token for token in normalize_text(target).split() if token]
    if not target_tokens:
        return 0.0
    text_tokens = set(normalize_text(text).split())
    if not text_tokens:
        return 0.0
    matches = sum(1 for token in target_tokens if token in text_tokens)
    return matches / len(target_tokens)


class MusicCandidateScorer:
    def score(
        self,
        *,
        media: MusicMediaInfo,
        query_build: QueryBuildResult,
        candidate: HostSearchCandidate,
        preferences: QueryPreferences,
    ) -> CandidateScoreResult:
        title_text = candidate.title
        main_title = media.title or media.album_title or (media.artist_names[0] if media.artist_names else media.provider_id)
        artist_name = " ".join(media.artist_names or media.album_artist_names) or main_title

        title_match = round(token_ratio(main_title, title_text) * 25, 2)
        artist_match = round(token_ratio(artist_name, title_text) * 20, 2)

        release_score = 0.0
        if media.entity_type == EntityType.ALBUM and media.album_title:
            release_score = round(token_ratio(media.album_title, title_text) * 15, 2)
        elif media.entity_type == EntityType.TRACK:
            release_score = round(token_ratio(media.title or main_title, title_text) * 15, 2)
        elif media.entity_type == EntityType.ARTIST:
            release_score = 10.0 if "discography" in normalize_text(title_text) else 6.0

        year_score = 10.0 if media.year and str(media.year) in title_text else 0.0
        format_score = self._format_quality_score(candidate)
        bitrate_score = self._bitrate_score(candidate, preferences)
        seeder_score = self._seeder_score(candidate.seeders)

        negative_hits = [
            clause.query
            for clause in query_build.negative_queries
            if clause.query and clause.query.lower() in title_text.lower()
        ]
        negative_penalty = min(len(negative_hits) * 12.0, 25.0)

        raw_score = round(
            title_match
            + artist_match
            + release_score
            + year_score
            + format_score
            + bitrate_score
            + seeder_score,
            2,
        )
        score_total = round(min(max(raw_score - negative_penalty, 0.0), 100.0), 2)

        breakdown = {
            "title_match": ScoreBreakdownItem(
                score=title_match,
                reason="标题命中度，基于 metadata 主标题与候选标题的分词比对。",
            ),
            "artist_match": ScoreBreakdownItem(
                score=artist_match,
                reason="艺人命中度，优先匹配主艺人名称。",
            ),
            "release_match": ScoreBreakdownItem(
                score=release_score,
                reason="专辑 / 歌曲 / 艺人上下文匹配度。",
            ),
            "year_match": ScoreBreakdownItem(
                score=year_score,
                reason="年份命中度，当前只做标题内年份比对。",
            ),
            "format_quality": ScoreBreakdownItem(
                score=format_score,
                reason="格式偏好得分，lossless / hi-res 高于有损格式。",
            ),
            "bitrate_preference": ScoreBreakdownItem(
                score=bitrate_score,
                reason="码率与无损偏好得分。",
            ),
            "seeder_availability": ScoreBreakdownItem(
                score=seeder_score,
                reason="做种数得分，优先更容易下载的候选。",
            ),
            "negative_keyword_penalty": ScoreBreakdownItem(
                score=-negative_penalty,
                reason=(
                    f"负向关键词惩罚，命中 {', '.join(negative_hits)}。"
                    if negative_hits
                    else "未命中负向关键词。"
                ),
            ),
        }

        reason_codes = [key for key, item in breakdown.items() if item.score > 0]
        if negative_hits:
            reason_codes.extend(f"negative:{keyword}" for keyword in negative_hits)

        decision = self._resolve_decision(
            score_total=score_total,
            preferences=preferences,
        )

        return CandidateScoreResult(
            raw_score=raw_score,
            score_total=score_total,
            score_breakdown=breakdown,
            decision=decision,
            reason_codes=reason_codes,
            dispatchable=decision in {DecisionStatus.AUTO_DOWNLOAD, DecisionStatus.MANUAL_CONFIRM},
        )

    @staticmethod
    def _format_quality_score(candidate: HostSearchCandidate) -> float:
        format_tag = (candidate.format_tag or "").lower()
        if format_tag in {"hires", "wav"}:
            return 17.0
        if format_tag in {"flac", "ape"}:
            return 15.0
        if format_tag == "aac":
            return 8.0
        if format_tag == "mp3":
            return 4.0
        return 3.0

    @staticmethod
    def _bitrate_score(candidate: HostSearchCandidate, preferences: QueryPreferences) -> float:
        bitrate = candidate.bitrate_kbps or 0
        format_tag = (candidate.format_tag or "").lower()
        if preferences.prefer_lossless and format_tag in {"flac", "ape", "wav", "hires"}:
            return 8.0
        if bitrate >= 320:
            return 6.0
        if bitrate >= 256:
            return 4.0
        if bitrate > 0:
            return 2.0
        return 0.0

    @staticmethod
    def _seeder_score(seeders: int) -> float:
        if seeders >= 20:
            return 8.0
        if seeders >= 10:
            return 6.0
        if seeders >= 5:
            return 4.0
        if seeders > 0:
            return 2.0
        return 0.0

    @staticmethod
    def _resolve_decision(*, score_total: float, preferences: QueryPreferences) -> DecisionStatus:
        if score_total >= preferences.auto_download_threshold:
            return DecisionStatus.AUTO_DOWNLOAD
        if score_total >= preferences.manual_confirm_threshold:
            return DecisionStatus.MANUAL_CONFIRM
        return DecisionStatus.REJECT
