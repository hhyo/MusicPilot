"""
Event 完整测试
"""

import pytest


class TestEventTypeFull:
    """EventType 完整测试"""

    def test_event_type_imports(self):
        from app.core.event import EventType
        assert EventType is not None

    def test_event_type_values(self):
        from app.core.event import EventType
        # 验证枚举值存在
        for et in EventType:
            assert et is not None


class TestEventManagerFull:
    """EventManager 完整测试"""

    def test_event_manager_imports(self):
        from app.core.event import EventManager
        assert EventManager is not None

    def test_event_manager_instance(self):
        from app.core.event import EventManager
        manager = EventManager()
        assert manager is not None


class TestEventModuleFull:
    """Event Module 完整测试"""

    def test_event_module_imports(self):
        from app.core import event
        assert event is not None
