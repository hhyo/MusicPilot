"""Repository layer for app settings persistence."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from ..models.settings import AppSettingModel


class SettingsRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_value(self, key: str) -> Any:
        model = self.session.get(AppSettingModel, key)
        if model is None:
            return None
        return model.value_json

    def set_value(self, key: str, value: Any) -> AppSettingModel:
        model = self.session.get(AppSettingModel, key)
        if model is None:
            model = AppSettingModel(key=key, value_json=value)
            self.session.add(model)
            return model

        model.value_json = value
        return model
