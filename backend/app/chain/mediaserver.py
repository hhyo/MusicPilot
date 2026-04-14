"""MoviePilot-aligned media server sync chain."""

from __future__ import annotations

from datetime import datetime, timezone

from . import MusicChainBase
from ..db.settings_oper import SettingsOper
from ..modules.host_http import HostTransportError


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MusicMediaServerChain(MusicChainBase):
    RUNTIME_STATE_KEY = "mediaserver_sync_runtime"

    def __init__(self, session, *, runtime) -> None:
        super().__init__(cache_region="music_mediaserver_chain")
        self.session = session
        self.runtime = runtime
        self.settings_oper = SettingsOper(session)

    def sync(self) -> dict:
        attempted_at = utc_now().isoformat()
        try:
            payload = dict(self.runtime.sync() or {})
        except HostTransportError as exc:
            payload = {
                "success": False,
                "sync_status": "unavailable",
                "message": str(exc),
                "libraries_synced": None,
                "integration_point": "MusicMediaServerChain.sync",
                "capability_source": "moviepilot.runtime.mediaserver_sync",
                "fallback_reason": exc.reason_code,
            }
        except Exception as exc:  # noqa: BLE001
            payload = {
                "success": False,
                "sync_status": "failed",
                "message": str(exc),
                "libraries_synced": None,
                "integration_point": "MusicMediaServerChain.sync",
                "capability_source": "moviepilot.runtime.mediaserver_sync",
                "fallback_reason": type(exc).__name__,
            }

        payload["attempted_at"] = attempted_at
        if payload.get("success"):
            payload.setdefault("sync_status", "synced")
            payload["synced_at"] = attempted_at
        else:
            payload.setdefault("sync_status", "failed")
            payload.setdefault("synced_at", None)

        self.settings_oper.set_value(self.RUNTIME_STATE_KEY, payload)
        self.session.flush()
        return payload

    def runtime_state(self) -> dict | None:
        value = self.settings_oper.get_value(self.RUNTIME_STATE_KEY)
        return dict(value) if isinstance(value, dict) else None
