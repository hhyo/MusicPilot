"""Aggregated dashboard summary service."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models.acquisition import DownloadBindingModel, SearchJobModel
from ..models.orchestration import OrganizeRecordModel, SubscriptionModel
from ..schemas.shared import DashboardSummary


class DashboardService:
    def __init__(self, session: Session):
        self.session = session

    def summary(self) -> DashboardSummary:
        return DashboardSummary(
            subscriptions_total=self._count(select(func.count()).select_from(SubscriptionModel)),
            jobs_running=self._count(
                select(func.count())
                .select_from(SearchJobModel)
                .where(SearchJobModel.status == "running")
            ),
            downloads_pending=self._count(
                select(func.count())
                .select_from(DownloadBindingModel)
                .where(
                    DownloadBindingModel.dispatch_status.in_(
                        [
                            "pending",
                            "awaiting_manual_confirmation",
                            "mock_submitted",
                            "host_submitted",
                        ]
                    )
                )
            ),
            organize_failed=self._count(
                select(func.count())
                .select_from(OrganizeRecordModel)
                .where(OrganizeRecordModel.organize_status == "failed")
            ),
        )

    def _count(self, statement) -> int:
        return int(self.session.scalar(statement) or 0)
