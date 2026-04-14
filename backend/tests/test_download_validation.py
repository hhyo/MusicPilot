from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.helper.download_validation import build_download_validation_report, ensure_fake_music_file


class DownloadValidationHelperTest(unittest.TestCase):
    def test_ensure_fake_music_file_writes_sanitized_flac(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            fake_path = ensure_fake_music_file(root, sample_name="Adele / Hello (Validation)")

            self.assertTrue(fake_path.exists())
            self.assertEqual(fake_path.suffix, ".flac")
            self.assertEqual(fake_path.parent.name, "adele-hello-validation")
            self.assertGreater(fake_path.stat().st_size, 0)

    def test_build_download_validation_report_marks_success(self) -> None:
        report = build_download_validation_report(
            host_base_url="http://127.0.0.1:3001",
            fake_source_path="/tmp/music-validation/hello.flac",
            downloader_name="Qbittorrent Validation",
            download_id="abc123",
            download_hash="abc123",
            path_handoff_status="resolved_from_history_download",
            organize_record_id="org-001",
            organize_status="applied",
        )

        self.assertEqual(report.overall_status, "success")
        self.assertEqual(report.download_submission.download_id, "abc123")
        self.assertEqual(report.history_handoff.download_hash, "abc123")
        self.assertEqual(report.organize_result.apply_status, "applied")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
