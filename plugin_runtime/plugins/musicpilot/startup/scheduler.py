"""Scheduler and local loop helpers for MoviePilot-aligned chains."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from ..core.config import settings
from ..core.dependencies import (
    build_music_chart_chain,
    build_music_subscribe_chain,
    build_music_transfer_chain,
    get_session_factory,
)

logger = logging.getLogger("musicpilot.scheduler")


def should_start_local_scheduler_loop() -> bool:
    if not settings.subscription_scheduler_enabled:
        return False
    return not __name__.startswith("app.plugins.musicpilot.")


def subscription_scheduler_interval_seconds() -> int:
    return max(1, int(round(settings.subscription_scheduler_poll_seconds)))


def chart_refresh_interval_minutes() -> int:
    return max(1, int(round(settings.chart_refresh_interval_minutes)))


def transfer_interval_seconds() -> int:
    return max(60, int(round(settings.host_handoff_retry_interval_seconds)))


def run_subscription_scheduler_once() -> dict:
    session_factory = get_session_factory()
    with session_factory() as session:
        try:
            chain = build_music_subscribe_chain(session)
            result = chain.run_pending_once()
            session.commit()
            if result.get("executed_ids"):
                logger.info("moviepilot.scheduler.executed ids=%s", ",".join(result["executed_ids"]))
            if result.get("error_ids"):
                logger.warning("moviepilot.scheduler.errors ids=%s", ",".join(result["error_ids"]))
            return result
        except Exception:  # noqa: BLE001
            session.rollback()
            logger.exception("moviepilot.scheduler.run_failed")
            raise


def run_chart_refresh_once() -> dict:
    session_factory = get_session_factory()
    with session_factory() as session:
        try:
            chain = build_music_chart_chain(session)
            result = chain.refresh_all_charts()
            session.commit()
            if result.get("refreshed_ids"):
                logger.info("moviepilot.chart_refresh.refreshed ids=%s", ",".join(result["refreshed_ids"]))
            if result.get("failed"):
                logger.warning("moviepilot.chart_refresh.failed ids=%s", ",".join(sorted(result["failed"].keys())))
            return result
        except Exception:  # noqa: BLE001
            session.rollback()
            logger.exception("moviepilot.chart_refresh.run_failed")
            raise


def run_transfer_once() -> dict:
    session_factory = get_session_factory()
    with session_factory() as session:
        try:
            chain = build_music_transfer_chain(session)
            result = chain.process()
            session.commit()
            diagnostics = result.get("diagnostics") or []
            if diagnostics:
                logger.info("moviepilot.transfer.processed count=%s", len(diagnostics))
            return result
        except Exception:  # noqa: BLE001
            session.rollback()
            logger.exception("moviepilot.transfer.run_failed")
            raise


async def run_interval_loop(
    *,
    runner: Callable[[], dict],
    interval_seconds: int,
    logger_key: str,
) -> None:
    while True:
        try:
            runner()
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            logger.exception("%s.loop_failed", logger_key)
        await asyncio.sleep(interval_seconds)


def build_local_scheduler_tasks() -> list[Awaitable[None]]:
    tasks: list[Awaitable[None]] = []
    if settings.subscription_scheduler_enabled:
        tasks.append(
            run_interval_loop(
                runner=run_subscription_scheduler_once,
                interval_seconds=subscription_scheduler_interval_seconds(),
                logger_key="subscription.scheduler",
            )
        )
    if settings.chart_refresh_enabled:
        tasks.append(
            run_interval_loop(
                runner=run_chart_refresh_once,
                interval_seconds=max(60, int(settings.chart_refresh_interval_minutes) * 60),
                logger_key="chart.refresh",
            )
        )
    if settings.host_handoff_retry_enabled:
        tasks.append(
            run_interval_loop(
                runner=run_transfer_once,
                interval_seconds=transfer_interval_seconds(),
                logger_key="music.transfer",
            )
        )
    return tasks
