"""Chart persistence models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ChartModel(Base):
    __tablename__ = "charts"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    chart_source: Mapped[str] = mapped_column(String(64), index=True)
    chart_name: Mapped[str] = mapped_column(String(255))
    chart_type: Mapped[str] = mapped_column(String(32), index=True)
    region: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    refresh_hint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    item_count: Mapped[int] = mapped_column(Integer, default=0)
    source_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_refreshed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_refresh_status: Mapped[str] = mapped_column(String(32), default="unknown", index=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    stale: Mapped[bool] = mapped_column(Boolean, default=True)
    mock: Mapped[bool] = mapped_column(Boolean, default=True)
    note: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    chart_group: Mapped[str | None] = mapped_column(String(64), nullable=True)
    chart_scope: Mapped[str | None] = mapped_column(String(64), nullable=True)
    freshness_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    supports_subscription: Mapped[bool] = mapped_column(Boolean, default=True)
    integration_point: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    items: Mapped[list["ChartItemModel"]] = relationship(
        back_populates="chart",
        cascade="all, delete-orphan",
        order_by="ChartItemModel.rank",
    )


class ChartItemModel(Base):
    __tablename__ = "chart_items"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    chart_id: Mapped[str] = mapped_column(ForeignKey("charts.id", ondelete="CASCADE"), index=True)
    chart_source: Mapped[str] = mapped_column(String(64), index=True)
    chart_name: Mapped[str] = mapped_column(String(255))
    rank: Mapped[int] = mapped_column(Integer, index=True)
    item_type: Mapped[str] = mapped_column(String(32), index=True)
    target_id: Mapped[str] = mapped_column(String(128), index=True)
    target_name: Mapped[str] = mapped_column(String(255))
    subtitle: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str] = mapped_column(String(64))
    source_type: Mapped[str] = mapped_column(String(64))
    target_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    mock: Mapped[bool] = mapped_column(Boolean, default=True)
    note: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    chart: Mapped[ChartModel] = relationship(back_populates="items")

