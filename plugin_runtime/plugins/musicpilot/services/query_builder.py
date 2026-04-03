"""Query builder for Phase 3 acquisition flow."""

from __future__ import annotations

from collections.abc import Iterable

from fastapi import HTTPException

from ..schemas.acquisition import (
    QueryBuildRequest,
    QueryBuildResult,
    QueryClause,
    QueryContext,
    QueryPreferences,
)
from ..schemas.metadata import MetadataDetail
from ..schemas.mvp import EntityType
from .metadata import MetadataService


DEFAULT_NEGATIVE_TERMS = ["karaoke", "instrumental", "tribute", "bootleg"]
INTEGRATION_POINT = "QueryBuilder 目前只输出结构化 PT 查询输入，待后续接入真实宿主搜索 adapter。"
TODO_ITEMS = [
    "后续可增加更多语言变体、版本策略和站点差异化查询模板。",
    "当前不会直接触发真实 PT 搜索，只生成稳定的查询结构。",
]


def _dedupe(items: Iterable[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        normalized = " ".join(item.split())
        if normalized and normalized not in result:
            result.append(normalized)
    return result


class QueryBuilderService:
    def __init__(self, metadata_service: MetadataService | None = None):
        self.metadata_service = metadata_service

    def build(self, payload: QueryBuildRequest) -> QueryBuildResult:
        if self.metadata_service is None:
            raise HTTPException(status_code=500, detail="Metadata service is not configured for query building.")

        detail = self.metadata_service.get_detail(payload.query_source_type, payload.query_source_id)
        return self.build_from_detail(detail, payload.preferences)

    @classmethod
    def build_from_detail(
        cls,
        detail: MetadataDetail,
        preferences: QueryPreferences | None = None,
    ) -> QueryBuildResult:
        resolved_preferences = preferences or QueryPreferences()
        format_terms = cls._preferred_format_terms(resolved_preferences)
        main_title = detail.track_title or detail.album_title or detail.title
        artist_name = detail.artist_name or detail.title

        canonical_queries: list[QueryClause] = []
        alias_queries: list[QueryClause] = []
        relaxed_queries: list[QueryClause] = []

        canonical_base = cls._entity_query_base(detail)
        if resolved_preferences.include_year and detail.year:
            canonical_queries.append(
                QueryClause(
                    query_type="canonical",
                    source="canonical_year",
                    query=" ".join(_dedupe(canonical_base + [str(detail.year)] + format_terms)),
                    explanation="标准查询词，包含主标题、艺人上下文、年份与偏好格式。",
                    priority=10,
                )
            )

        canonical_queries.append(
            QueryClause(
                query_type="canonical",
                source="canonical_title",
                query=" ".join(_dedupe(canonical_base + format_terms)),
                explanation="标准查询词，优先使用结构化 metadata 的主标题与偏好格式。",
                priority=20,
            )
        )

        if detail.entity_type == EntityType.TRACK and detail.album_title:
            canonical_queries.append(
                QueryClause(
                    query_type="canonical",
                    source="canonical_track_album",
                    query=" ".join(_dedupe([artist_name, main_title, detail.album_title] + format_terms)),
                    explanation="标准查询词，歌曲搜索额外保留专辑上下文以减少误匹配。",
                    priority=30,
                )
            )

        if resolved_preferences.include_aliases:
            alias_seed = detail.aliases[:4]
            for index, alias in enumerate(alias_seed, start=1):
                if detail.entity_type == EntityType.ARTIST:
                    alias_parts = [alias]
                else:
                    alias_parts = [artist_name, alias]
                alias_queries.append(
                    QueryClause(
                        query_type="alias",
                        source="alias_metadata",
                        query=" ".join(_dedupe(alias_parts + format_terms)),
                        explanation="别名查询词，来自 metadata aliases 字段。",
                        priority=40 + index,
                    )
                )

        relaxed_queries.extend(cls._build_relaxed_queries(detail, format_terms))

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
            query_source_type=detail.entity_type,
            query_source_id=detail.id,
            entity_title=detail.title,
            artist_name=detail.artist_name,
            album_title=detail.album_title,
            track_title=detail.track_title,
            year=detail.year,
            release_type=detail.release_type.value if detail.release_type else None,
            aliases=detail.aliases,
            genres=detail.genres,
            external_ids=detail.external_ids,
            provider=detail.provider,
            source_type=detail.source_type,
            note=detail.note,
            summary=(
                f"{detail.entity_type.value} metadata 已生成 {len(ordered_queries)} 条正向查询词与 "
                f"{len(negative_queries)} 条负向过滤词，供后续 PT 搜索 adapter 消费。"
            ),
        )

        return QueryBuildResult(
            query_source_type=detail.entity_type,
            query_source_id=detail.id,
            provider=detail.provider,
            source_type=detail.source_type,
            mock=detail.mock,
            preferences=resolved_preferences,
            canonical_queries=canonical_queries,
            alias_queries=alias_queries,
            relaxed_queries=relaxed_queries,
            negative_queries=negative_queries,
            ordered_queries=ordered_queries,
            query_context=context,
            note="当前 QueryBuilder 基于 metadata detail 构造稳定查询词，不直接调用真实宿主搜索。",
            integration_point=INTEGRATION_POINT,
            todo=TODO_ITEMS,
        )

    @staticmethod
    def _preferred_format_terms(preferences: QueryPreferences) -> list[str]:
        if preferences.preferred_formats:
            return preferences.preferred_formats[:2]
        if preferences.prefer_lossless:
            return ["FLAC"]
        return []

    @staticmethod
    def _entity_query_base(detail: MetadataDetail) -> list[str]:
        if detail.entity_type == EntityType.ARTIST:
            return [detail.title]
        if detail.entity_type == EntityType.ALBUM:
            return [detail.artist_name or "", detail.title]
        return [detail.artist_name or "", detail.title]

    @classmethod
    def _build_relaxed_queries(cls, detail: MetadataDetail, format_terms: list[str]) -> list[QueryClause]:
        relaxed_queries: list[QueryClause] = []
        artist_name = detail.artist_name or detail.title
        main_title = detail.track_title or detail.album_title or detail.title

        relaxed_queries.append(
            QueryClause(
                query_type="relaxed",
                source="relaxed_primary",
                query=" ".join(_dedupe([artist_name, main_title])),
                explanation="宽松查询词，保留艺人 + 主标题，不附加年份与格式。",
                priority=60,
            )
        )

        if detail.entity_type == EntityType.TRACK and detail.album_title:
            relaxed_queries.append(
                QueryClause(
                    query_type="relaxed",
                    source="relaxed_track_only",
                    query=" ".join(_dedupe([detail.title])),
                    explanation="宽松查询词，歌曲场景仅保留主标题，作为兜底查询。",
                    priority=70,
                )
            )
        elif detail.entity_type == EntityType.ALBUM:
            relaxed_queries.append(
                QueryClause(
                    query_type="relaxed",
                    source="relaxed_album_only",
                    query=" ".join(_dedupe([detail.title] + format_terms)),
                    explanation="宽松查询词，专辑场景保留专辑标题与格式偏好。",
                    priority=70,
                )
            )
        else:
            relaxed_queries.append(
                QueryClause(
                    query_type="relaxed",
                    source="relaxed_artist_only",
                    query=" ".join(_dedupe([detail.title])),
                    explanation="宽松查询词，艺人场景仅保留艺人名。",
                    priority=70,
                )
            )

        return relaxed_queries
