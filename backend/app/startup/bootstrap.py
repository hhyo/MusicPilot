"""Startup bootstrap helpers for MusicPilot runtime."""

from __future__ import annotations

from ..modules.metadata import MetadataBootstrapSummary, bootstrap_metadata_storage
from ..modules.metadata_provider import MetadataProviderAdapter


def bootstrap_runtime_storage(
    *,
    reseed: bool = False,
    provider: MetadataProviderAdapter | None = None,
) -> MetadataBootstrapSummary:
    return bootstrap_metadata_storage(reseed=reseed, provider=provider)
