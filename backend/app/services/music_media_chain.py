"""Unified upper-layer music media parsing chain."""

from __future__ import annotations

from ..schemas.music_media import MusicMediaInput, MusicResolveDetailResponse
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

    def resolve(self, input: MusicMediaInput):
        normalized = self.input_adapter.from_input(input)
        base = self.base_builder.build(normalized)
        return self.recognizer.recognize(base)

    def resolve_detail(self, input: MusicMediaInput) -> MusicResolveDetailResponse:
        media = self.resolve(input)
        detail = self.hydrator.hydrate(media)
        return MusicResolveDetailResponse(media=media, detail=detail)
