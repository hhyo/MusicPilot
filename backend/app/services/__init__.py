"""Service layer placeholders.

TODO(Phase 1+):
- ChartService
- MetadataService
- SubscriptionService
- AcquisitionService
- OrganizerService
"""
"""Service exports for backend business modules."""

from .metadata import MetadataService

__all__ = ["MetadataService"]
