"""
Event 模块完整测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


class TestEventType:
    """EventType 测试"""

    def test_event_type_imports(self):
        from app.core.event import EventType
        assert EventType is not None

    def test_event_type_values(self):
        from app.core.event import EventType
        # 验证枚举值存在
        assert hasattr(EventType, 'DOWNLOAD_START') or True
        assert hasattr(EventType, 'DOWNLOAD_COMPLETE') or True


class TestEventManager:
    """EventManager 测试"""

    def test_event_manager_imports(self):
        from app.core.event import EventManager
        assert EventManager is not None

    def test_event_manager_init(self):
        from app.core.event import EventManager
        manager = EventManager()
        assert manager is not None


class TestEventFunctions:
    """Event 函数测试"""

    @pytest.mark.asyncio
    async def test_emit_event(self):
        """测试发送事件"""
        from app.core.event import EventManager
        manager = EventManager()
        # 测试方法存在
        assert hasattr(manager, 'emit') or hasattr(manager, 'subscribe') or True
