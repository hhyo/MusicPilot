"""Music layout planning helpers for organize preview/apply flows."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from ..schemas.metadata import MetadataDetail
from ..schemas.orchestration import OrganizeStrategySnapshot


class MusicLayoutPlanner:
    def build_relative_path(
        self,
        *,
        snapshot: OrganizeStrategySnapshot,
        context: dict[str, str],
        metadata_detail: MetadataDetail | None,
    ) -> str:
        if metadata_detail is None or metadata_detail.entity_type == "artist":
            return self.render_template(snapshot.artist_dir_template, context)

        if metadata_detail.entity_type == "album":
            return self.render_template(snapshot.album_dir_template, context)

        album_dir = self.render_template(snapshot.album_dir_template, context)
        track_file = self.render_template(snapshot.track_file_template, context)
        return str(PurePosixPath(album_dir) / track_file)

    def render_template(self, template: str, context: dict[str, str]) -> str:
        rendered = template
        for key, value in context.items():
            rendered = rendered.replace(f"{{{key}}}", value)
        rendered = re.sub(r"/{2,}", "/", rendered).strip("/")
        return rendered or "unknown"
