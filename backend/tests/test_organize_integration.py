"""Unit tests for organize plan building and explicit host failure behavior."""

from __future__ import annotations

import unittest

from fastapi import HTTPException

from app.adapters.organize import OrganizeAdapter
from app.schemas.integration import AdapterMode
from app.schemas.orchestration import OrganizeAdapterResult, OrganizeStatus
from app.services.host_integration import HostIntegrationService, OrganizeAdapterResolver
from app.services.organize_strategy import OrganizeStrategyService

from test_host_integration import DummyProbeAdapter, build_candidate, build_settings
from test_query_builder import build_album_detail


class DummyMockOrganizeAdapter(OrganizeAdapter):
    def preview(self, *, candidate, metadata_detail, binding_id=None, plan):  # type: ignore[override]
        return OrganizeAdapterResult(
            organizeable=True,
            organize_backend=AdapterMode.MOCK,
            adapter_mode=AdapterMode.MOCK,
            strategy=plan.strategy,
            strategy_snapshot=plan.strategy_snapshot,
            organize_status=OrganizeStatus.PREVIEW_READY,
            target_library_path=plan.target_library_path,
            target_relative_path=plan.target_relative_path,
            strategy_note=plan.strategy_note,
            integration_point="DummyMockOrganizeAdapter.preview",
            mock=True,
            note="mock preview",
        )

    def apply(self, *, organize_job_id, candidate, metadata_detail, binding_id=None, plan):  # type: ignore[override]
        return OrganizeAdapterResult(
            organizeable=True,
            organize_backend=AdapterMode.MOCK,
            adapter_mode=AdapterMode.MOCK,
            strategy=plan.strategy,
            strategy_snapshot=plan.strategy_snapshot,
            organize_status=OrganizeStatus.APPLIED,
            target_library_path=plan.target_library_path,
            target_relative_path=plan.target_relative_path,
            strategy_note=plan.strategy_note,
            integration_point="DummyMockOrganizeAdapter.apply",
            mock=True,
            note="mock apply",
        )


class DummyBrokenHostOrganizeAdapter(OrganizeAdapter):
    def preview(self, *, candidate, metadata_detail, binding_id=None, plan):  # type: ignore[override]
        raise RuntimeError("host organize preview boom")

    def apply(self, *, organize_job_id, candidate, metadata_detail, binding_id=None, plan):  # type: ignore[override]
        raise RuntimeError("host organize apply boom")


class OrganizeIntegrationTest(unittest.TestCase):
    def test_strategy_service_builds_album_relative_path(self) -> None:
        candidate = build_candidate()
        detail = build_album_detail()
        service = OrganizeStrategyService(build_settings())

        plan = service.build_plan(candidate=candidate, metadata_detail=detail)

        self.assertIn("adele", plan.target_relative_path)
        self.assertIn("2015", plan.target_relative_path)
        self.assertIn("25", plan.target_relative_path)
        self.assertTrue(plan.target_library_path.endswith(plan.target_relative_path))

    def test_runtime_state_reports_strict_host_organize_blocking_reason(self) -> None:
        service = HostIntegrationService(
            settings=build_settings(
                host_organize_strategy="strict_host",
                host_fallback_to_mock=False,
            ),
            probe_adapter=DummyProbeAdapter(),
        )

        runtime = service.runtime_state()

        self.assertEqual(runtime.active_organize_adapter, "real_organize")
        self.assertEqual(runtime.organize_fallback_reason, "strict_host_required:host_capability_unavailable")

    def test_prefer_host_organize_preview_raises_on_runtime_error(self) -> None:
        detail = build_album_detail()
        candidate = build_candidate()
        plan = OrganizeStrategyService(build_settings()).build_plan(candidate=candidate, metadata_detail=detail)
        service = HostIntegrationService(
            settings=build_settings(
                host_organize_strategy="prefer_host",
                host_assume_organize_available=True,
            ),
            probe_adapter=DummyProbeAdapter(),
        )
        resolver = OrganizeAdapterResolver(
            integration_service=service,
            mock_adapter=DummyMockOrganizeAdapter(),
            host_adapter=DummyBrokenHostOrganizeAdapter(),
        )

        with self.assertRaises(HTTPException) as ctx:
            resolver.preview(candidate=candidate, metadata_detail=detail, binding_id=None, plan=plan)

        self.assertEqual(ctx.exception.status_code, 503)
        self.assertIn("host_organize_preview_runtime_error:RuntimeError", str(ctx.exception.detail))

    def test_prefer_host_organize_apply_raises_on_runtime_error(self) -> None:
        detail = build_album_detail()
        candidate = build_candidate()
        plan = OrganizeStrategyService(build_settings()).build_plan(candidate=candidate, metadata_detail=detail)
        service = HostIntegrationService(
            settings=build_settings(
                host_organize_strategy="prefer_host",
                host_assume_organize_available=True,
            ),
            probe_adapter=DummyProbeAdapter(),
        )
        resolver = OrganizeAdapterResolver(
            integration_service=service,
            mock_adapter=DummyMockOrganizeAdapter(),
            host_adapter=DummyBrokenHostOrganizeAdapter(),
        )

        with self.assertRaises(HTTPException) as ctx:
            resolver.apply(
                organize_job_id="org-001",
                candidate=candidate,
                metadata_detail=detail,
                binding_id=None,
                plan=plan,
            )

        self.assertEqual(ctx.exception.status_code, 503)
        self.assertIn("host_organize_apply_runtime_error:RuntimeError", str(ctx.exception.detail))

    def test_strict_host_organize_preview_raises_when_capability_missing(self) -> None:
        detail = build_album_detail()
        candidate = build_candidate()
        plan = OrganizeStrategyService(build_settings()).build_plan(candidate=candidate, metadata_detail=detail)
        service = HostIntegrationService(
            settings=build_settings(host_organize_strategy="strict_host"),
            probe_adapter=DummyProbeAdapter(),
        )
        resolver = OrganizeAdapterResolver(
            integration_service=service,
            mock_adapter=DummyMockOrganizeAdapter(),
            host_adapter=DummyBrokenHostOrganizeAdapter(),
        )

        with self.assertRaises(HTTPException):
            resolver.preview(candidate=candidate, metadata_detail=detail, binding_id=None, plan=plan)


if __name__ == "__main__":
    unittest.main()
