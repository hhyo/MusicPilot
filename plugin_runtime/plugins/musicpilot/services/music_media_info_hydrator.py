"""Hydrate recognized music media objects into rich metadata detail."""

from __future__ import annotations

import httpx
from fastapi import HTTPException


class MusicMediaInfoHydrator:
    """Loads detail views from recognized media objects."""

    def __init__(self, metadata_service):
        self.metadata_service = metadata_service

    def hydrate(self, media):
        try:
            return self.metadata_service.get_detail(media.entity_type, media.provider_id)
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail="Metadata provider detail request failed.") from exc
