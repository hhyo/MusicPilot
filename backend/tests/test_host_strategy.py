"""Unit tests for Phase 9 matrix-aware host strategy decisions."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from app.schemas.acquisition import PathHandoffInfo
from app.schemas.integration import VerificationState
from app.schemas.validation import (
    HostValidationMatrixEntry,
    HostValidationMatrixReport,
    HostValidationMatrixSummary,
)
from app.services.host_strategy import HostStrategyService

from test_host_integration import build_candidate


class FakeValidationMatrixService:
    def load_report(self) -> HostValidationMatrixReport:
        samples = [
            HostValidationMatrixEntry(
                sample_id="ordinary_accident_title_add",
                sample_name="ordinary_accident_title_add",
                search_input_type="search/title",
                dispatch_endpoint_type="download_add",
                path_handoff_source="moviepilot.runtime.history.download",
                path_handoff_status="resolved_from_history_download",
                transfer_name_result="success",
                transfer_manual_result="success",
                organize_result="applied",
                verification_state=VerificationState.VERIFIED,
                stability_state="single_sample",
                attempt_count=1,
                success_count=1,
                note="single sample success",
            ),
            HostValidationMatrixEntry(
                sample_id="transfer_replay_1",
                sample_name="transfer_replay_1",
                search_input_type="history/transfer",
                dispatch_endpoint_type=None,
                path_handoff_source="moviepilot.runtime.history.transfer",
                path_handoff_status="resolved_from_history_transfer",
                transfer_name_result="success",
                transfer_manual_result="success",
                organize_result="applied",
                verification_state=VerificationState.VERIFIED,
                stability_state="stable",
                attempt_count=2,
                success_count=2,
                note="stable success",
            ),
            HostValidationMatrixEntry(
                sample_id="ordinary_accident_media",
                sample_name="ordinary_accident_media",
                search_input_type="search/media",
                dispatch_endpoint_type="download_media",
                path_handoff_source="moviepilot.runtime.history.download",
                path_handoff_status="resolved_from_history_download",
                transfer_name_result="success",
                transfer_manual_result="failed",
                organize_result="failed",
                verification_state=VerificationState.UNVERIFIED,
                stability_state="blocked",
                blocker="没有找到可整理的媒体文件",
                note="blocked sample",
            ),
        ]
        return HostValidationMatrixReport(
            phase="Phase 8",
            generated_at=datetime.now(timezone.utc),
            samples=samples,
            summary=HostValidationMatrixSummary(
                generated_at=datetime.now(timezone.utc),
                sample_count=3,
                stable_count=1,
                single_sample_count=1,
                blocked_count=1,
                flaky_count=0,
                verified_count=2,
                unverified_count=1,
                placeholder_count=0,
                note="test summary",
            ),
            note="test report",
        )


class HostStrategyServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.service = HostStrategyService(validation_matrix_service=FakeValidationMatrixService())  # type: ignore[arg-type]

    def test_summary_exposes_preferred_paths(self) -> None:
        summary = self.service.summary()

        self.assertEqual(summary.preferred_dispatch_endpoint, "download_add")
        self.assertEqual(summary.preferred_handoff_source, "resolved_from_history_transfer")
        self.assertIn("download_media + resolved_from_history_download -> organize apply", summary.blocked_paths)

    def test_dispatch_prefers_download_add_when_media_reference_exists(self) -> None:
        candidate = build_candidate()
        candidate.raw_payload = {"host_media_reference": {"tmdbid": 1456349}}

        decision = self.service.recommend_dispatch(candidate)

        self.assertEqual(decision.selected_path, "download_add")
        self.assertEqual(decision.matrix_status, "single_sample")

    def test_handoff_marks_transfer_history_as_stable(self) -> None:
        handoff = PathHandoffInfo(
            download_hash="abc",
            source_path="/downloads/movie/Argentina.1985.2022.WEB-DL.1080p.mkv",
            source_filetype="file",
            source_name="Argentina.1985.2022.WEB-DL.1080p.mkv",
            source_basename="Argentina.1985.2022.WEB-DL.1080p",
            source_extension=".mkv",
            handoff_source="moviepilot.runtime.history.transfer",
            handoff_status="resolved_from_history_transfer",
            verification_state=VerificationState.VERIFIED,
            note="stable",
            raw_summary={},
        )

        decision = self.service.evaluate_handoff(handoff=handoff, dispatch_endpoint_type="download_media")

        self.assertEqual(decision.matrix_status, "stable")
        self.assertFalse(decision.blocked)

    def test_organize_apply_blocks_download_media_plus_download_history(self) -> None:
        handoff = PathHandoffInfo(
            download_hash="abc",
            source_path="/downloads/movie/ordinary-accident",
            source_filetype="dir",
            source_name="ordinary-accident",
            source_basename="ordinary-accident",
            source_extension="",
            handoff_source="moviepilot.runtime.history.download",
            handoff_status="resolved_from_history_download",
            verification_state=VerificationState.VERIFIED,
            note="blocked",
            raw_summary={},
        )

        decision = self.service.evaluate_organize_apply(
            handoff=handoff,
            dispatch_endpoint_type="download_media",
        )

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.recommended_action, "block_apply")


if __name__ == "__main__":
    unittest.main()
