"""Unified upper-layer music media parsing chain."""

from __future__ import annotations

from . import MusicChainBase
from ..schemas.music_media import (
    MusicMediaInfo,
    MusicMediaInput,
    MusicMediaSourceKind,
    MusicMetaBase,
    MusicPrepareResponse,
    MusicRecognitionAssessment,
    MusicResolveDetailResponse,
    MusicResolveResponse,
)
from ..schemas.orchestration import ChartEntryInfo, ChartInfo
from ..helper.media_hydration import MusicMediaHydrator
from ..helper.media_input import MusicMediaInputHelper
from ..helper.media_recognition import MusicMediaRecognizer
from ..helper.meta_base import MusicMetaBaseBuilder


class MusicMediaChain(MusicChainBase):
    """Owns the shared input -> meta base -> media info flow."""

    def __init__(self, metadata_module, metadata_provider):
        super().__init__(cache_region="music_media_chain")
        self.metadata_module = metadata_module
        self.metadata_provider = metadata_provider
        self.input_helper = MusicMediaInputHelper()
        self.base_builder = MusicMetaBaseBuilder()
        self.recognizer = MusicMediaRecognizer(
            metadata_module=metadata_module,
            metadata_provider=metadata_provider,
        )
        self.hydrator = MusicMediaHydrator(metadata_module=metadata_module)

    @property
    def active_provider(self) -> str:
        return self.recognizer.metadata_provider.provider

    def search_metadata(self, payload):
        return self.metadata_module.search(payload)

    def build_base(self, input: MusicMediaInput):
        normalized = self.input_helper.from_input(input)
        return self.base_builder.build(normalized)

    def assess(self, base: MusicMetaBase) -> MusicRecognitionAssessment:
        return self.recognizer.assess(base)

    def prepare(self, input: MusicMediaInput) -> MusicPrepareResponse:
        base = self.build_base(input)
        assessment = self.assess(base)
        return MusicPrepareResponse(input=input, base=base, assessment=assessment)

    def resolve_base(self, base: MusicMetaBase) -> MusicMediaInfo:
        return self.recognizer.recognize(base)

    def input_from_discovery_entry(self, chart: ChartInfo, entry: ChartEntryInfo) -> MusicMediaInput:
        return self.input_helper.from_discovery_entry(chart, entry)

    def prepare_from_discovery_entry(self, chart: ChartInfo, entry: ChartEntryInfo) -> MusicPrepareResponse:
        input_payload = self.input_from_discovery_entry(chart, entry)
        return self.prepare(input_payload)

    def input_from_music_media_info(
        self,
        payload: MusicMediaInfo,
        *,
        source_kind: str | MusicMediaSourceKind,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ) -> MusicMediaInput:
        return self.input_helper.from_music_media_info(
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
        source_kind: str | MusicMediaSourceKind,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ) -> MusicMediaInput:
        return self.input_helper.from_provider_ref(
            entity_type=entity_type,
            provider=provider,
            provider_id=provider_id,
            source_kind=source_kind,
            source_context=source_context,
            raw_context=raw_context,
        )

    def input_from_active_provider_ref(
        self,
        *,
        entity_type,
        provider_id: str,
        source_kind: str | MusicMediaSourceKind,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ) -> MusicMediaInput:
        return self.input_from_provider_ref(
            entity_type=entity_type,
            provider=self.active_provider,
            provider_id=provider_id,
            source_kind=source_kind,
            source_context=source_context,
            raw_context=raw_context,
        )

    def prepare_from_provider_ref(
        self,
        *,
        entity_type,
        provider: str,
        provider_id: str,
        source_kind: str | MusicMediaSourceKind,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ) -> MusicPrepareResponse:
        input_payload = self.input_from_provider_ref(
            entity_type=entity_type,
            provider=provider,
            provider_id=provider_id,
            source_kind=source_kind,
            source_context=source_context,
            raw_context=raw_context,
        )
        return self.prepare(input_payload)

    def prepare_from_active_provider_ref(
        self,
        *,
        entity_type,
        provider_id: str,
        source_kind: str | MusicMediaSourceKind,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ) -> MusicPrepareResponse:
        input_payload = self.input_from_active_provider_ref(
            entity_type=entity_type,
            provider_id=provider_id,
            source_kind=source_kind,
            source_context=source_context,
            raw_context=raw_context,
        )
        return self.prepare(input_payload)

    def input_from_target_payload_ref(
        self,
        *,
        entity_type,
        target_id: str,
        target_payload: dict | None,
        source_kind: str | MusicMediaSourceKind,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ) -> MusicMediaInput:
        return self.input_helper.from_target_payload_ref(
            entity_type=entity_type,
            target_id=target_id,
            target_payload=target_payload,
            source_kind=source_kind,
            source_context=source_context,
            raw_context=raw_context,
        )

    def prepare_from_target_payload_ref(
        self,
        *,
        entity_type,
        target_id: str,
        target_payload: dict | None,
        source_kind: str | MusicMediaSourceKind,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ) -> MusicPrepareResponse:
        input_payload = self.input_from_target_payload_ref(
            entity_type=entity_type,
            target_id=target_id,
            target_payload=target_payload,
            source_kind=source_kind,
            source_context=source_context,
            raw_context=raw_context,
        )
        return self.prepare(input_payload)

    def resolve(self, input: MusicMediaInput):
        base = self.build_base(input)
        return self.resolve_base(base)

    def resolve_from_provider_ref(
        self,
        *,
        entity_type,
        provider: str,
        provider_id: str,
        source_kind: str | MusicMediaSourceKind,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ) -> MusicMediaInfo:
        input_payload = self.input_from_provider_ref(
            entity_type=entity_type,
            provider=provider,
            provider_id=provider_id,
            source_kind=source_kind,
            source_context=source_context,
            raw_context=raw_context,
        )
        return self.resolve(input_payload)

    def resolve_from_active_provider_ref(
        self,
        *,
        entity_type,
        provider_id: str,
        source_kind: str | MusicMediaSourceKind,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ) -> MusicMediaInfo:
        input_payload = self.input_from_active_provider_ref(
            entity_type=entity_type,
            provider_id=provider_id,
            source_kind=source_kind,
            source_context=source_context,
            raw_context=raw_context,
        )
        return self.resolve(input_payload)

    def resolve_from_target_payload_ref(
        self,
        *,
        entity_type,
        target_id: str,
        target_payload: dict | None,
        source_kind: str | MusicMediaSourceKind,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ) -> MusicMediaInfo:
        input_payload = self.input_from_target_payload_ref(
            entity_type=entity_type,
            target_id=target_id,
            target_payload=target_payload,
            source_kind=source_kind,
            source_context=source_context,
            raw_context=raw_context,
        )
        return self.resolve(input_payload)

    def resolve_response_from_base(self, base: MusicMetaBase) -> MusicResolveResponse:
        assessment = self.recognizer.assess(base)
        media = self.resolve_base(base)
        return MusicResolveResponse(base=base, assessment=assessment, media=media)

    def resolve_response(self, input: MusicMediaInput) -> MusicResolveResponse:
        prepared = self.prepare(input)
        media = self.resolve_base(prepared.base)
        return MusicResolveResponse(base=prepared.base, assessment=prepared.assessment, media=media)

    def resolve_response_from_provider_ref(
        self,
        *,
        entity_type,
        provider: str,
        provider_id: str,
        source_kind: str | MusicMediaSourceKind,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ) -> MusicResolveResponse:
        input_payload = self.input_from_provider_ref(
            entity_type=entity_type,
            provider=provider,
            provider_id=provider_id,
            source_kind=source_kind,
            source_context=source_context,
            raw_context=raw_context,
        )
        return self.resolve_response(input_payload)

    def resolve_response_from_target_payload_ref(
        self,
        *,
        entity_type,
        target_id: str,
        target_payload: dict | None,
        source_kind: str | MusicMediaSourceKind,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ) -> MusicResolveResponse:
        input_payload = self.input_from_target_payload_ref(
            entity_type=entity_type,
            target_id=target_id,
            target_payload=target_payload,
            source_kind=source_kind,
            source_context=source_context,
            raw_context=raw_context,
        )
        return self.resolve_response(input_payload)

    def resolve_response_from_active_provider_ref(
        self,
        *,
        entity_type,
        provider_id: str,
        source_kind: str | MusicMediaSourceKind,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ) -> MusicResolveResponse:
        input_payload = self.input_from_active_provider_ref(
            entity_type=entity_type,
            provider_id=provider_id,
            source_kind=source_kind,
            source_context=source_context,
            raw_context=raw_context,
        )
        return self.resolve_response(input_payload)

    def resolve_detail_from_provider_ref(
        self,
        *,
        entity_type,
        provider: str,
        provider_id: str,
        source_kind: str | MusicMediaSourceKind,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ) -> MusicResolveDetailResponse:
        input_payload = self.input_from_provider_ref(
            entity_type=entity_type,
            provider=provider,
            provider_id=provider_id,
            source_kind=source_kind,
            source_context=source_context,
            raw_context=raw_context,
        )
        return self.resolve_detail(input_payload)

    def resolve_detail_from_active_provider_ref(
        self,
        *,
        entity_type,
        provider_id: str,
        source_kind: str | MusicMediaSourceKind,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ) -> MusicResolveDetailResponse:
        input_payload = self.input_from_active_provider_ref(
            entity_type=entity_type,
            provider_id=provider_id,
            source_kind=source_kind,
            source_context=source_context,
            raw_context=raw_context,
        )
        return self.resolve_detail(input_payload)

    def resolve_detail_from_target_payload_ref(
        self,
        *,
        entity_type,
        target_id: str,
        target_payload: dict | None,
        source_kind: str | MusicMediaSourceKind,
        source_context: dict | None = None,
        raw_context: dict | None = None,
    ) -> MusicResolveDetailResponse:
        input_payload = self.input_from_target_payload_ref(
            entity_type=entity_type,
            target_id=target_id,
            target_payload=target_payload,
            source_kind=source_kind,
            source_context=source_context,
            raw_context=raw_context,
        )
        return self.resolve_detail(input_payload)

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
