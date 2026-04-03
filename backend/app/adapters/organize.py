"""Adapter boundary for organize preview in Phase 4."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from ..schemas.acquisition import SearchCandidateDetail
from ..schemas.metadata import MetadataDetail
from ..schemas.orchestration import OrganizeAdapterResult, OrganizeStatus


def slugify(value: str | None) -> str:
    if not value:
        return "unknown"
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip()).strip("-").lower()
    return normalized or "unknown"


class OrganizeAdapter(ABC):
    @abstractmethod
    def preview(
        self,
        *,
        candidate: SearchCandidateDetail,
        metadata_detail: MetadataDetail | None,
        binding_id: str | None = None,
    ) -> OrganizeAdapterResult:
        """Return a mock organize preview for the current candidate or binding."""


class MockOrganizeAdapter(OrganizeAdapter):
    def preview(
        self,
        *,
        candidate: SearchCandidateDetail,
        metadata_detail: MetadataDetail | None,
        binding_id: str | None = None,
    ) -> OrganizeAdapterResult:
        entity_folder = "library"
        title_folder = slugify(candidate.title)

        if metadata_detail is not None:
            artist_folder = slugify(metadata_detail.artist_name or metadata_detail.title)
            if metadata_detail.entity_type == "album":
                entity_folder = f"{artist_folder}/albums/{slugify(metadata_detail.title)}"
            elif metadata_detail.entity_type == "track":
                entity_folder = f"{artist_folder}/tracks/{slugify(metadata_detail.title)}"
            else:
                entity_folder = f"artists/{slugify(metadata_detail.title)}"
            title_folder = slugify(metadata_detail.title)

        binding_hint = f" via binding {binding_id}" if binding_id else ""
        return OrganizeAdapterResult(
            organizeable=True,
            organize_status=OrganizeStatus.PREVIEW_READY,
            target_library_path=f"/library/musicpilot/mock/{entity_folder}/{title_folder}",
            strategy_note=(
                "当前仅生成 organize preview，不执行真实文件移动、硬链接、标签写入或媒体库刷新。"
                f"{binding_hint}"
            ),
            integration_point=(
                "Replace MockOrganizeAdapter with a verified organize pipeline after downloader completion, "
                "filesystem rules, and library refresh contracts are confirmed."
            ),
            mock=True,
            note="当前为 mock organize boundary，结果仅用于状态流转与后续接入点说明。",
        )
