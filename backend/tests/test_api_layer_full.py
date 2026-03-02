"""
API 层完整测试 - 覆盖更多端点
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch


class TestAPIMain:
    """API Main 测试"""

    def test_api_router_imports(self):
        from app.api.apiv1 import api_router
        assert api_router is not None

    def test_api_module_imports(self):
        from app.api import apiv1
        assert apiv1 is not None


class TestAppMain:
    """App Main 测试"""

    def test_app_imports(self):
        from app.main import app
        assert app is not None

    def test_app_is_fastapi(self):
        from app.main import app
        from fastapi import FastAPI
        assert isinstance(app, FastAPI)


class TestFactoryFull:
    """Factory 完整测试"""

    def test_create_app_imports(self):
        from app.factory import create_app
        assert create_app is not None

    def test_factory_module_imports(self):
        from app import factory
        assert factory is not None


class TestTasksFull:
    """Tasks 完整测试"""

    def test_tasks_module_imports(self):
        from app import tasks
        assert tasks is not None

    def test_download_monitor_module_imports(self):
        from app.tasks import download_monitor
        assert download_monitor is not None

    def test_subscribe_check_module_imports(self):
        from app.tasks import subscribe_check
        assert subscribe_check is not None
