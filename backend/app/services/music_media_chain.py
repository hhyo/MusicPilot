"""Unified upper-layer music media parsing chain."""

from __future__ import annotations

from ..schemas.music_media import MusicMediaInput, MusicResolveDetailResponse, MusicResolveResponse
from ..schemas.music_media import MusicMediaInfo, MusicMetaBase, MusicRecognitionAssessment
from ..schemas.orchestration import ChartEntryInfo, ChartInfo
from .music_media_info_hydrator import MusicMediaInfoHydrator
from .music_media_input_adapter import MusicMediaInputAdapter
from .music_media_recognizer import MusicMediaRecognizer
from .music_meta_base_builder import MusicMetaBaseBuilder


class MusicMediaChain:
    """Owns the shared input -> meta base -> media info flow."""

    def __init__(self, metadata_service, metadata_adapter):
        self.input_adapter = MusicMediaInputAdapter()
        self.base_builder = MusicMetaBaseBuilder()
        self.recognizer = MusicMediaRecognizer(
            metadata_service=metadata_service,
            metadata_adapter=metadata_adapter,
        )
        self.hydrator = MusicMediaInfoHydrator(metadata_service=metadata_service)

    def build_base(self, input: MusicMediaInput):
        normalized = self.input_adapter.from_input(input)
        return self.base_builder.build(normalized)

    def assess(self, base: MusicMetaBase) -> MusicRecognitionAssessment:
        return self.recognizer.assess(base)

    def input_from_discovery_entry(self, chart: ChartInfo, entry: ChartEntryInfo) -> MusicMediaInput:
        return self.input_adapter.from_discovery_entry(chart, entry)

    def input_from_music_media_info(
        self,
        payload: MusicMediaInfo,
        *,
        source_kind: str,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ) -> MusicMediaInput:
        return self.input_adapter.from_music_media_info(
            payload,
            source_kind=source_kind,
            source_context=source_context,
            raw_context=raw_context,
        )

    def input_from_provider_ref(
        self,
        *,
        entity_type,
        provider: str,
        provider_id: str,
        source_kind: str,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ) -> MusicMediaInput:
        return self.input_adapter.from_provider_ref(
            entity_type=entity_type,
            provider=provider,
            provider_id=provider_id,
            source_kind=source_kind,
            source_context=source_context,
            raw_context=raw_context,
        )

    def resolve(self, input: MusicMediaInput):
        base = self.build_base(input)
        return self.recognizer.recognize(base)

    def resolve_response(self, input: MusicMediaInput) -> MusicResolveResponse:
        base = self.build_base(input)
        assessment = self.recognizer.assess(base)
        media = self.recognizer.recognize(base)
        return MusicResolveResponse(base=base, assessment=assessment, media=media)

    def resolve_detail(self, input: MusicMediaInput) -> MusicResolveDetailResponse:
        resolved = self.resolve_response(input)
        media = resolved.media
        detail = self.hydrate(media)
        return MusicResolveDetailResponse(
            base=resolved.base,
            assessment=resolved.assessment,
            media=media,
            detail=detail,
        )

    def hydrate(self, media: MusicMediaInfo):
        return self.hydrator.hydrate(media)
