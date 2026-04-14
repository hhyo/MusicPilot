"""Music organize plan assembly for preview/apply flows."""

from __future__ import annotations

from pathlib import PurePosixPath

from ..core.config import Settings
from ..schemas.acquisition import SearchCandidateDetail
from ..schemas.metadata import MetadataDetail
from ..schemas.orchestration import OrganizeConflictPolicy, OrganizePlan, OrganizeStrategySnapshot
from ..utils.music_layout import MusicLayoutPlanner
from ..utils.music_metadata import MusicMetadataRecognizer


class MusicOrganizeStrategy:
    def __init__(
        self,
        settings: Settings,
        *,
        metadata_recognizer: MusicMetadataRecognizer | None = None,
        layout_planner: MusicLayoutPlanner | None = None,
    ):
        self.settings = settings
        self.metadata_recognizer = metadata_recognizer or MusicMetadataRecognizer()
        self.layout_planner = layout_planner or MusicLayoutPlanner()

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
                "Current organize mapping uses a small built-in template set and is designed "
                "to remain stable until a verified host organize contract is available."
            ),
        )

        metadata = self.metadata_recognizer.recognize(candidate=candidate, metadata_detail=metadata_detail)
        context = {
            "artist_name": metadata.artist_name,
            "album_title": metadata.album_title,
            "track_title": metadata.track_title,
            "title": metadata.title,
            "year": metadata.year,
            "format_ext": metadata.format_ext,
        }
        target_relative_path = self.layout_planner.build_relative_path(
            snapshot=snapshot,
            context=context,
            metadata_detail=metadata_detail,
        )
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
