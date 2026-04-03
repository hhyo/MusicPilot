"""Read the latest real-host validation matrix exported by manual verification scripts."""

from __future__ import annotations

import json
from pathlib import Path

from ..core.config import Settings
from ..schemas.validation import HostValidationMatrixReport, HostValidationMatrixSummary


class HostValidationMatrixService:
    def __init__(self, *, settings: Settings):
        self.settings = settings
        self.matrix_path = Path(settings.host_validation_matrix_path)

    def load_report(self) -> HostValidationMatrixReport | None:
        if not self.matrix_path.exists():
            return None
        payload = json.loads(self.matrix_path.read_text(encoding="utf-8"))
        return HostValidationMatrixReport.model_validate(payload)

    def summary(self) -> HostValidationMatrixSummary | None:
        report = self.load_report()
        if report is None:
            return None
        return report.summary
