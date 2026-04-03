"""Unit tests for host-aware adapter resolution with explicit failure semantics."""

from __future__ import annotations

import unittest

from fastapi import HTTPException

from app.adapters.download_dispatch import DownloadDispatchAdapter
from app.adapters.host_probe import HostProbeAdapter
from app.adapters.host_search import HostSearchAdapter, normalize_title
from app.core.config import Settings
from app.schemas.acquisition import DispatchAdapterResult, HostSearchCandidate, QueryBuildResult, SearchCandidateDetail
from app.schemas.integration import AdapterMode, AdapterStrategy, VerificationState
from app.schemas.probe import (
    ProbeCapabilitySummary,
    ProbeConfigPayload,
    ProbeConfigRequest,
    ProbeDispatchPayload,
    ProbeDispatchRequest,
    ProbeDownloadersPayload,
    ProbeDownloaderItem,
    ProbeHealthPayload,
    ProbeNotifyPayload,
    ProbeNotifyRequest,
    ProbeSearchPayload,
    ProbeSearchRequest,
    ProbeSitesPayload,
    ProbeSiteItem,
)
from app.services.host_integration import DispatchAdapterResolver, HostIntegrationService, HostSearchAdapterResolver
from app.services.query_builder import QueryBuilderService

from test_query_builder import build_album_detail


class DummyProbeAdapter(HostProbeAdapter):
    def __init__(
        self,
        *,
        host_online: bool | None = True,
        search_capability: bool | None = True,
        sites_visible: bool | None = True,
        downloaders_available: bool | None = True,
    ) -> None:
        self.host_online = host_online
        self.search_capability = search_capability
        self.sites_visible = sites_visible
        self.downloaders_available = downloaders_available

    def _summary(self, capability: str, available: bool | None) -> ProbeCapabilitySummary:
        return ProbeCapabilitySummary(
            capability=capability,
            status="unverified" if available else "degraded",
            host_online=self.host_online if capability == "health" else None,
            capability_available=available,
            adapter_mode=AdapterMode.HOST,
            active_strategy=AdapterStrategy.PREFER_HOST,
            host_integration_enabled=True,
            capability_source="test.probe",
            verification_state=VerificationState.UNVERIFIED,
            integration_point=f"DummyProbeAdapter.{capability}",
            note="test probe",
            todo=[],
        )

    def probe_health(self) -> ProbeHealthPayload:
        return ProbeHealthPayload(
            summary=self._summary("health", self.host_online),
            checks={"host_online": self.host_online, "plugin_api_registered": True, "note": "test"},
        )

    def list_sites(self) -> ProbeSitesPayload:
        items = (
            [ProbeSiteItem(id="site-1", name="Test Site", enabled=True, visibility="unverified", note="test")]
            if self.sites_visible
            else []
        )
        return ProbeSitesPayload(summary=self._summary("sites", self.sites_visible), items=items)

    def probe_search(self, payload: ProbeSearchRequest) -> ProbeSearchPayload:
        return ProbeSearchPayload(
            summary=self._summary("search", self.search_capability),
            query_echo=payload.model_dump(mode="json"),
            sample_result_fields=["title"],
            sample_result_count=1 if self.search_capability else 0,
        )

    def list_downloaders(self) -> ProbeDownloadersPayload:
        items = (
            [ProbeDownloaderItem(id="dl-1", name="Test Downloader", is_default=True, status="unverified", note="test")]
            if self.downloaders_available
            else []
        )
        return ProbeDownloadersPayload(
            summary=self._summary("downloaders", self.downloaders_available),
            items=items,
        )

    def probe_dispatch(self, payload: ProbeDispatchRequest) -> ProbeDispatchPayload:
        return ProbeDispatchPayload(
            summary=self._summary("dispatch", self.downloaders_available),
            request_echo=payload.model_dump(mode="json"),
            dispatch_preview={"accepted": bool(self.downloaders_available)},
        )

    def probe_notify(self, payload: ProbeNotifyRequest) -> ProbeNotifyPayload:
        return ProbeNotifyPayload(
            summary=self._summary("notify", False),
            request_echo=payload.model_dump(mode="json"),
            notification_preview={"sent": False},
        )

    def probe_config(self, payload: ProbeConfigRequest) -> ProbeConfigPayload:
        return ProbeConfigPayload(
            summary=self._summary("config", False),
            operation=payload.operation,
            request_echo=payload.model_dump(mode="json"),
            config_preview={"persisted": False},
        )

    def config_summary(self) -> ProbeConfigPayload:
        payload = ProbeConfigRequest()
        return self.probe_config(payload)

    def search_summary(self) -> ProbeSearchPayload:
        payload = ProbeSearchRequest()
        return self.probe_search(payload)


class DummyMockSearchAdapter(HostSearchAdapter):
    def search(self, *, query_build: QueryBuildResult, detail):  # type: ignore[override]
        return [
            HostSearchCandidate(
                site_id="mock-site",
                site_name="Mock Site",
                title=f"{detail.artist_name} - {detail.title}",
                normalized_title=normalize_title(f"{detail.artist_name} - {detail.title}"),
                size_bytes=1,
                seeders=1,
                peers=1,
                format_tag="flac",
                bitrate_kbps=1000,
                source_tags=["mock"],
                mock=True,
                note="mock fallback candidate",
                raw_payload={},
            )
        ]


class DummyBrokenHostSearchAdapter(HostSearchAdapter):
    def search(self, *, query_build: QueryBuildResult, detail):  # type: ignore[override]
        raise RuntimeError("host search boom")


class DummyMockDispatchAdapter(DownloadDispatchAdapter):
    def dispatch(self, *, candidate: SearchCandidateDetail, downloader_id: str, manual_confirm: bool) -> DispatchAdapterResult:
        return DispatchAdapterResult(
            dispatchable=True,
            dispatch_status="mock_submitted",
            target_downloader=downloader_id,
            note="mock fallback dispatch",
            integration_point="DummyMockDispatchAdapter.dispatch",
            mock=True,
        )


class DummyBrokenHostDispatchAdapter(DownloadDispatchAdapter):
    def dispatch(self, *, candidate: SearchCandidateDetail, downloader_id: str, manual_confirm: bool) -> DispatchAdapterResult:
        raise RuntimeError("host dispatch boom")


def build_settings(**overrides: object) -> Settings:
    base = {
        "host_integration_enabled": True,
        "host_search_strategy": "prefer_host",
        "host_dispatch_strategy": "prefer_host",
        "host_fallback_to_mock": True,
        "host_verification_state": "unverified",
    }
    base.update(overrides)
    return Settings(**base)


def build_candidate() -> SearchCandidateDetail:
    return SearchCandidateDetail(
        id="cand-001",
        job_id="job-001",
        site_id="site-001",
        site_name="Test Site",
        title="Adele - 25",
        normalized_title="adele 25",
        size_bytes=1,
        seeders=1,
        peers=1,
        format_tag="flac",
        bitrate_kbps=1000,
        source_tags=["lossless"],
        raw_score=100,
        score_total=100,
        score_breakdown={},
        decision="auto_download",
        reason_codes=[],
        dispatchable=True,
        dispatch_status="pending",
        mock=False,
        note="candidate",
        created_at="2026-04-03T00:00:00Z",  # type: ignore[arg-type]
    )


class HostIntegrationServiceTest(unittest.TestCase):
    def test_runtime_state_stays_observable_when_strict_host_is_unavailable(self) -> None:
        service = HostIntegrationService(
            settings=build_settings(
                host_search_strategy="strict_host",
                host_dispatch_strategy="strict_host",
                host_fallback_to_mock=False,
            ),
            probe_adapter=DummyProbeAdapter(
                host_online=False,
                search_capability=False,
                sites_visible=False,
                downloaders_available=False,
            ),
        )

        runtime = service.runtime_state()

        self.assertEqual(runtime.active_search_adapter, "real_host_search")
        self.assertEqual(runtime.active_dispatch_adapter, "real_download_dispatch")
        self.assertEqual(runtime.search_fallback_reason, "strict_host_required:host_capability_unavailable")
        self.assertEqual(runtime.dispatch_fallback_reason, "strict_host_required:host_capability_unavailable")

    def test_prefer_host_search_raises_on_runtime_error(self) -> None:
        detail = build_album_detail()
        query_build = QueryBuilderService.build_from_detail(detail)
        service = HostIntegrationService(
            settings=build_settings(),
            probe_adapter=DummyProbeAdapter(),
        )
        resolver = HostSearchAdapterResolver(
            integration_service=service,
            mock_adapter=DummyMockSearchAdapter(),
            host_adapter=DummyBrokenHostSearchAdapter(),
        )

        with self.assertRaises(HTTPException) as ctx:
            resolver.search(query_build=query_build, detail=detail)

        self.assertEqual(ctx.exception.status_code, 503)
        self.assertIn("host_search_runtime_error:RuntimeError", str(ctx.exception.detail))

    def test_prefer_host_dispatch_raises_on_runtime_error(self) -> None:
        service = HostIntegrationService(
            settings=build_settings(),
            probe_adapter=DummyProbeAdapter(),
        )
        resolver = DispatchAdapterResolver(
            integration_service=service,
            mock_adapter=DummyMockDispatchAdapter(),
            host_adapter=DummyBrokenHostDispatchAdapter(),
        )

        with self.assertRaises(HTTPException) as ctx:
            resolver.dispatch(
                candidate=build_candidate(),
                downloader_id="mock-downloader",
                manual_confirm=True,
            )

        self.assertEqual(ctx.exception.status_code, 503)
        self.assertIn("host_dispatch_runtime_error:RuntimeError", str(ctx.exception.detail))

    def test_prefer_host_search_raises_when_capability_is_unavailable(self) -> None:
        detail = build_album_detail()
        query_build = QueryBuilderService.build_from_detail(detail)
        service = HostIntegrationService(
            settings=build_settings(),
            probe_adapter=DummyProbeAdapter(search_capability=False),
        )
        resolver = HostSearchAdapterResolver(
            integration_service=service,
            mock_adapter=DummyMockSearchAdapter(),
            host_adapter=DummyBrokenHostSearchAdapter(),
        )

        with self.assertRaises(HTTPException) as ctx:
            resolver.search(query_build=query_build, detail=detail)

        self.assertEqual(ctx.exception.status_code, 503)
        self.assertIn("host_capability_unavailable", str(ctx.exception.detail))

    def test_strict_host_search_raises_when_capability_is_unavailable(self) -> None:
        detail = build_album_detail()
        query_build = QueryBuilderService.build_from_detail(detail)
        service = HostIntegrationService(
            settings=build_settings(host_search_strategy="strict_host"),
            probe_adapter=DummyProbeAdapter(search_capability=False),
        )
        resolver = HostSearchAdapterResolver(
            integration_service=service,
            mock_adapter=DummyMockSearchAdapter(),
            host_adapter=DummyBrokenHostSearchAdapter(),
        )

        with self.assertRaises(HTTPException):
            resolver.search(query_build=query_build, detail=detail)


if __name__ == "__main__":
    unittest.main()
