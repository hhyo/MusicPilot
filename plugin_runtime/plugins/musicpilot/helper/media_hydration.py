"""Hydrate recognized music media objects into rich metadata detail."""

from __future__ import annotations

import httpx
from fastapi import HTTPException


class MusicMediaHydrator:
    """Loads detail views from recognized media objects."""

    def __init__(self, metadata_module):
        self.metadata_module = metadata_module

    def hydrate(self, media):
        try:
            return self.metadata_module.get_detail_by_provider_ref(
                entity_type=media.entity_type,
                provider=media.provider,
                provider_id=media.provider_id,
            )
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail="Metadata provider detail request failed.") from exc
