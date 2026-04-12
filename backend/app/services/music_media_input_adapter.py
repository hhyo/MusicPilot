"""Scenario input adapters for the unified music media chain."""

from __future__ import annotations

from ..schemas.music_media import MusicMediaInput


class MusicMediaInputAdapter:
    """Normalizes upstream payloads into the shared input model."""

    def from_input(self, payload: MusicMediaInput) -> MusicMediaInput:
        return payload
