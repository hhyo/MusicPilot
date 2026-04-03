"""Organize strategy mapping for Phase 6 host-aware organize flows."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from ..core.config import Settings
from ..schemas.acquisition import SearchCandidateDetail
from ..schemas.metadata import MetadataDetail
from ..schemas.orchestration import (
    OrganizeConflictPolicy,
    OrganizePlan,
    OrganizeStrategySnapshot,
)


def slugify(value: str | None) -> str:
    if not value:
        return "unknown"
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip()).strip("-").lower()
    return normalized or "unknown"


class OrganizeStrategyService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def build_plan(
        self,
        *,
        candidate: SearchCandidateDetail,
        metadata_detail: MetadataDetail | None,
    ) -> OrganizePlan:
        snapshot = OrganizeStrategySnapshot(
            strategy_name="music_default_layout",
            library_type=self.settings.organize_library_type,
            root_path=self.settings.organize_root_path,
            artist_dir_template=self.settings.organize_artist_dir_template,
            album_dir_template=self.settings.organize_album_dir_template,
            track_file_template=self.settings.organize_track_file_template,
            conflict_policy=OrganizeConflictPolicy(self.settings.organize_conflict_policy),
            template_note=(
                "Current organize mapping uses a small placeholder-safe template set and is designed "
                "to remain stable until a verified host organize contract is available."
            ),
        )

        context = self._build_context(candidate=candidate, metadata_detail=metadata_detail)
        target_relative_path = self._resolve_relative_path(snapshot=snapshot, context=context, metadata_detail=metadata_detail)
        target_library_path = str(PurePosixPath(snapshot.root_path) / target_relative_path)

        return OrganizePlan(
            strategy=snapshot.strategy_name,
            strategy_snapshot=snapshot,
            target_library_path=target_library_path,
            target_relative_path=target_relative_path,
            strategy_note=(
                f"Resolved with {snapshot.strategy_name}: artist template `{snapshot.artist_dir_template}`, "
                f"album template `{snapshot.album_dir_template}`, track template `{snapshot.track_file_template}`."
            ),
        )

    def _resolve_relative_path(
        self,
        *,
        snapshot: OrganizeStrategySnapshot,
        context: dict[str, str],
        metadata_detail: MetadataDetail | None,
    ) -> str:
        if metadata_detail is None:
            return self._render_template(snapshot.artist_dir_template, context)

        if metadata_detail.entity_type == "artist":
            return self._render_template(snapshot.artist_dir_template, context)

        if metadata_detail.entity_type == "album":
            return self._render_template(snapshot.album_dir_template, context)

        album_dir = self._render_template(snapshot.album_dir_template, context)
        track_file = self._render_template(snapshot.track_file_template, context)
        return str(PurePosixPath(album_dir) / track_file)

    def _build_context(
        self,
        *,
        candidate: SearchCandidateDetail,
        metadata_detail: MetadataDetail | None,
    ) -> dict[str, str]:
        title = metadata_detail.title if metadata_detail else candidate.title
        artist_name = (
            metadata_detail.artist_name
            if metadata_detail and metadata_detail.artist_name
            else (metadata_detail.title if metadata_detail and metadata_detail.entity_type == "artist" else candidate.site_name)
        )
        album_title = (
            metadata_detail.album_title
            if metadata_detail and metadata_detail.album_title
            else (metadata_detail.title if metadata_detail and metadata_detail.entity_type == "album" else title)
        )
        track_title = (
            metadata_detail.track_title
            if metadata_detail and metadata_detail.track_title
            else (metadata_detail.title if metadata_detail and metadata_detail.entity_type == "track" else title)
        )
        year = str(metadata_detail.year) if metadata_detail and metadata_detail.year else "unknown"
        format_ext = slugify(candidate.format_tag or "bin")

        return {
            "artist_name": slugify(artist_name),
            "album_title": slugify(album_title),
            "track_title": slugify(track_title),
            "title": slugify(title),
            "year": year,
            "format_ext": format_ext,
        }

    def _render_template(self, template: str, context: dict[str, str]) -> str:
        rendered = template
        for key, value in context.items():
            rendered = rendered.replace(f"{{{key}}}", value)
        rendered = re.sub(r"/{2,}", "/", rendered).strip("/")
        return rendered or "unknown"
