"""Query builder centered on formal MusicMediaInfo objects."""

from __future__ import annotations

from collections.abc import Iterable

from fastapi import HTTPException

from ..schemas.acquisition import (
    QueryExecutionPlan,
    QueryBuildRequest,
    QueryBuildResult,
    QueryClause,
    QueryContext,
    QueryPreferences,
)
from ..schemas.music_media import MusicMediaInfo
from ..schemas.shared import EntityType


DEFAULT_NEGATIVE_TERMS = ["karaoke", "instrumental", "tribute", "bootleg"]
INTEGRATION_POINT = "QueryBuilder 当前围绕 MusicMediaInfo 输出结构化 PT 查询输入，并为 host search adapter 提供执行级上下文。"


def _dedupe(items: Iterable[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        normalized = " ".join(item.split())
        if normalized and normalized not in result:
            result.append(normalized)
    return result


class QueryBuilderService:
    def __init__(self, music_media_chain=None):
        self.music_media_chain = music_media_chain

    def build(self, payload: QueryBuildRequest) -> QueryBuildResult:
        if self.music_media_chain is None:
            raise HTTPException(status_code=500, detail="Music media chain is not configured for query building.")
        media = self.music_media_chain.resolve(payload.input)
        return self.build_from_music_media_info(media, payload.preferences)

    @classmethod
    def build_queries_from_music_media_info(
        cls,
        media_info: MusicMediaInfo,
        preferences: QueryPreferences | None = None,
    ) -> list[str]:
        result = cls.build_from_music_media_info(media_info, preferences)
        return [query.query for query in result.ordered_queries if query.query_type != "negative"]

    @classmethod
    def build_from_music_media_info(
        cls,
        media_info: MusicMediaInfo,
        preferences: QueryPreferences | None = None,
    ) -> QueryBuildResult:
        resolved_preferences = preferences or QueryPreferences()
        format_terms = cls._preferred_format_terms(resolved_preferences)

        canonical_queries = cls._build_canonical_queries(
            media=media_info,
            format_terms=format_terms,
            include_year=resolved_preferences.include_year,
        )
        alias_queries = cls._build_alias_queries(media_info, format_terms)
        relaxed_queries = cls._build_relaxed_queries(media_info, format_terms)

        negative_terms = list(DEFAULT_NEGATIVE_TERMS)
        if not resolved_preferences.allow_live:
            negative_terms.append("live")
        if not resolved_preferences.allow_remaster:
            negative_terms.append("remaster")
        negative_terms.extend(resolved_preferences.negative_keywords)
        negative_queries = [
            QueryClause(
                query_type="negative",
                source="negative_filter",
                query=term,
                explanation="负向过滤词，用于后续宿主搜索 adapter 或评分阶段剔除高风险误匹配。",
                priority=80 + index,
            )
            for index, term in enumerate(_dedupe(negative_terms), start=1)
        ]

        ordered_queries = sorted(
            canonical_queries + alias_queries + relaxed_queries,
            key=lambda item: item.priority,
        )

        context = QueryContext(
            entity_type=media_info.entity_type,
            provider=media_info.provider,
            provider_id=media_info.provider_id,
            title=media_info.title or media_info.album_title or (media_info.artist_names[0] if media_info.artist_names else media_info.provider_id),
            artist_names=list(media_info.artist_names),
            album_title=media_info.album_title,
            album_artist_names=list(media_info.album_artist_names),
            year=media_info.year,
            track_number=media_info.track_number,
            disc_number=media_info.disc_number,
            external_refs=dict(media_info.external_refs),
            match_strategy=media_info.match_strategy,
            note=(
                "当前 QueryBuilder 已切到统一音乐媒体解析链上游，直接消费识别后的 MusicMediaInfo。"
            ),
            summary=(
                f"{media_info.entity_type.value} media 已生成 {len(ordered_queries)} 条正向查询词与 "
                f"{len(negative_queries)} 条负向过滤词，供后续 PT 搜索 adapter 消费。"
            ),
        )

        return QueryBuildResult(
            entity_type=media_info.entity_type,
            provider=media_info.provider,
            provider_id=media_info.provider_id,
            music_media_info=media_info,
            mock=False,
            search_ready=bool(ordered_queries),
            preferences=resolved_preferences,
            canonical_queries=canonical_queries,
            alias_queries=alias_queries,
            relaxed_queries=relaxed_queries,
            negative_queries=negative_queries,
            ordered_queries=ordered_queries,
            execution_plan=QueryExecutionPlan(
                ready=bool(ordered_queries),
                positive_query_count=len(ordered_queries),
                negative_term_count=len(negative_queries),
                top_positive_queries=[query.query for query in ordered_queries[:4]],
                negative_terms=[query.query for query in negative_queries],
                note="执行计划会按 ordered_queries 顺序交给 host search adapter，negative_terms 用于评分与误匹配过滤。",
            ),
            query_context=context,
            note="当前 QueryBuilder 基于 MusicMediaInfo 构造稳定查询词，并输出可直接交给 host search adapter 的执行计划。",
            integration_point=INTEGRATION_POINT,
        )

    @staticmethod
    def _preferred_format_terms(preferences: QueryPreferences) -> list[str]:
        if preferences.preferred_formats:
            return preferences.preferred_formats[:2]
        if preferences.prefer_lossless:
            return ["FLAC"]
        return []

    @staticmethod
    def _primary_artist(media: MusicMediaInfo) -> str:
        artist_terms = _dedupe(media.artist_names or media.album_artist_names)
        return " ".join(artist_terms) or (media.title or media.album_title or media.provider_id)

    @classmethod
    def _canonical_main_title(cls, media: MusicMediaInfo) -> str:
        if media.entity_type == EntityType.ALBUM:
            return media.album_title or media.title or cls._primary_artist(media)
        return media.title or media.album_title or cls._primary_artist(media)

    @classmethod
    def _build_alias_queries(cls, media: MusicMediaInfo, format_terms: list[str]) -> list[QueryClause]:
        aliases = media.release_context.get("aliases") if isinstance(media.release_context, dict) else None
        if not isinstance(aliases, list):
            return []

        primary_artist = cls._primary_artist(media)
        result: list[QueryClause] = []
        for index, alias in enumerate(_dedupe(str(value) for value in aliases if value), start=1):
            alias_parts = [alias] if media.entity_type == EntityType.ARTIST else [primary_artist, alias]
            result.append(
                QueryClause(
                    query_type="alias",
                    source="alias_release_context",
                    query=" ".join(_dedupe(alias_parts + format_terms)),
                    explanation="别名查询词，来自统一媒体对象中的 release_context aliases。",
                    priority=80 + index,
                )
            )
        return result

    @classmethod
    def _build_canonical_queries(
        cls,
        *,
        media: MusicMediaInfo,
        format_terms: list[str],
        include_year: bool,
    ) -> list[QueryClause]:
        canonical_queries: list[QueryClause] = []
        primary_artist = cls._primary_artist(media)
        main_title = cls._canonical_main_title(media)

        if media.entity_type == EntityType.ARTIST:
            canonical_queries.append(
                QueryClause(
                    query_type="canonical",
                    source="canonical_title",
                    query=" ".join(_dedupe([media.title or primary_artist])),
                    explanation="标准查询词，艺人场景优先保留艺人名本身。",
                    priority=10,
                )
            )
            if include_year and media.year:
                canonical_queries.append(
                    QueryClause(
                        query_type="canonical",
                        source="canonical_year",
                        query=" ".join(_dedupe([media.title or primary_artist, str(media.year)])),
                        explanation="标准查询词，艺人场景把年份降级为补充限定条件。",
                        priority=65,
                    )
                )
            return canonical_queries

        canonical_queries.append(
            QueryClause(
                query_type="canonical",
                source="canonical_title",
                query=" ".join(_dedupe([primary_artist, main_title] + format_terms)),
                explanation="标准查询词，优先对齐 PT 常见的艺人 + 主标题 + 格式 release title。",
                priority=10,
            )
        )

        if media.entity_type == EntityType.ALBUM:
            if include_year and media.year:
                canonical_queries.append(
                    QueryClause(
                        query_type="canonical",
                        source="canonical_year",
                        query=" ".join(_dedupe([primary_artist, main_title, str(media.year)] + format_terms)),
                        explanation="标准查询词，在专辑场景补充年份以贴近常见 PT 专辑标题。",
                        priority=20,
                    )
                )
            return canonical_queries

        if media.album_title:
            canonical_queries.append(
                QueryClause(
                    query_type="canonical",
                    source="canonical_album_release",
                    query=" ".join(_dedupe([primary_artist, media.album_title] + format_terms)),
                    explanation="标准查询词，歌曲场景优先补一条专辑包查询，贴近 PT 常见整专资源标题。",
                    priority=20,
                )
            )
            canonical_queries.append(
                QueryClause(
                    query_type="canonical",
                    source="canonical_track_album",
                    query=" ".join(_dedupe([primary_artist, main_title, media.album_title] + format_terms)),
                    explanation="标准查询词，歌曲搜索额外保留专辑上下文以减少误匹配。",
                    priority=30,
                )
            )

        if include_year and media.year:
            canonical_queries.append(
                QueryClause(
                    query_type="canonical",
                    source="canonical_year",
                    query=" ".join(_dedupe([primary_artist, main_title, str(media.year)] + format_terms)),
                    explanation="标准查询词，歌曲场景把年份降级为补充限定条件。",
                    priority=65,
                )
            )

        return canonical_queries

    @classmethod
    def _build_relaxed_queries(cls, media: MusicMediaInfo, format_terms: list[str]) -> list[QueryClause]:
        relaxed_queries: list[QueryClause] = []
        primary_artist = cls._primary_artist(media)
        main_title = cls._canonical_main_title(media)

        relaxed_queries.append(
            QueryClause(
                query_type="relaxed",
                source="relaxed_primary",
                query=" ".join(_dedupe([primary_artist, main_title])),
                explanation="宽松查询词，保留艺人 + 主标题，不附加年份与格式。",
                priority=50,
            )
        )

        if media.entity_type == EntityType.TRACK and media.album_title:
            relaxed_queries.append(
                QueryClause(
                    query_type="relaxed",
                    source="relaxed_album_release",
                    query=" ".join(_dedupe([primary_artist, media.album_title])),
                    explanation="宽松查询词，歌曲场景补一条艺人 + 专辑标题，覆盖整专资源命名。",
                    priority=60,
                )
            )
            relaxed_queries.append(
                QueryClause(
                    query_type="relaxed",
                    source="relaxed_track_only",
                    query=" ".join(_dedupe([media.title or main_title])),
                    explanation="宽松查询词，歌曲场景仅保留主标题，作为兜底查询。",
                    priority=70,
                )
            )
        elif media.entity_type == EntityType.ALBUM:
            relaxed_queries.append(
                QueryClause(
                    query_type="relaxed",
                    source="relaxed_album_only",
                    query=" ".join(_dedupe([main_title] + format_terms)),
                    explanation="宽松查询词，专辑场景保留专辑标题与格式偏好。",
                    priority=60,
                )
            )
            relaxed_queries.append(
                QueryClause(
                    query_type="relaxed",
                    source="relaxed_title_only",
                    query=" ".join(_dedupe([main_title])),
                    explanation="宽松查询词，专辑场景仅保留专辑标题。",
                    priority=70,
                )
            )
        else:
            relaxed_queries.append(
                QueryClause(
                    query_type="relaxed",
                    source="relaxed_artist_only",
                    query=" ".join(_dedupe([media.title or primary_artist])),
                    explanation="宽松查询词，艺人场景仅保留艺人名。",
                    priority=70,
                )
            )

        return relaxed_queries
