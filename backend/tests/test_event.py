"""
EventManager 单元测试
测试事件管理器的功能
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.event import EventManager, EventType, event_bus


class TestEventType:
    """EventType 枚举测试"""

    def test_event_type_values(self):
        """测试事件类型枚举值"""
        assert EventType.MetadataRecognized == "metadata.recognized"
        assert EventType.DownloadStarted == "download.started"
        assert EventType.SystemStarted == "system.started"

    def test_event_type_str_conversion(self):
        """测试事件类型字符串转换"""
        event_type = EventType.DownloadCompleted
        assert str(event_type) == "download.completed"
        assert event_type.value == "download.completed"


class TestEventManager:
    """EventManager 测试类"""

    @pytest.fixture
    def manager(self):
        """创建新的事件管理器实例"""
        return EventManager()

    # ==================== register 测试 ====================

    def test_register_handler(self, manager):
        """测试注册事件处理器"""
        handler = MagicMock()

        manager.register("test_event", handler)

        assert "test_event" in manager._handlers
        assert handler in manager._handlers["test_event"]

    def test_register_multiple_handlers(self, manager):
        """测试注册多个处理器"""
        handler1 = MagicMock()
        handler2 = MagicMock()

        manager.register("test_event", handler1)
        manager.register("test_event", handler2)

        assert len(manager._handlers["test_event"]) == 2

    # ==================== unregister 测试 ====================

    def test_unregister_handler(self, manager):
        """测试取消注册事件处理器"""
        handler = MagicMock()
        manager.register("test_event", handler)

        manager.unregister("test_event", handler)

        assert handler not in manager._handlers["test_event"]

    def test_unregister_nonexistent_handler(self, manager):
        """测试取消注册不存在的处理器（不应报错）"""
        handler = MagicMock()

        # 不应抛出异常
        manager.unregister("nonexistent_event", handler)

    def test_unregister_from_empty_list(self, manager):
        """测试从空列表取消注册"""
        handler = MagicMock()

        # 不应抛出异常
        manager.unregister("empty_event", handler)

    # ==================== send_event 测试 ====================

    def test_send_event_calls_handler(self, manager):
        """测试发送事件调用处理器"""
        handler = MagicMock()
        manager.register("test_event", handler)

        manager.send_event("test_event", {"key": "value"})

        handler.assert_called_once_with({"key": "value"})

    def test_send_event_no_handlers(self, manager):
        """测试发送没有处理器的事件（不应报错）"""
        # 不应抛出异常
        manager.send_event("no_handlers_event", {"data": "test"})

    def test_send_event_multiple_handlers(self, manager):
        """测试发送事件调用多个处理器"""
        handler1 = MagicMock()
        handler2 = MagicMock()
        manager.register("test_event", handler1)
        manager.register("test_event", handler2)

        manager.send_event("test_event", {"test": "data"})

        handler1.assert_called_once()
        handler2.assert_called_once()

    def test_send_event_handler_exception(self, manager):
        """测试处理器抛出异常时不影响其他处理器"""
        handler1 = MagicMock(side_effect=Exception("Handler error"))
        handler2 = MagicMock()
        manager.register("test_event", handler1)
        manager.register("test_event", handler2)

        # 不应抛出异常
        manager.send_event("test_event", {})

        # 两个处理器都应该被调用
        handler1.assert_called_once()
        handler2.assert_called_once()

    def test_send_event_with_none_data(self, manager):
        """测试发送事件数据为None"""
        handler = MagicMock()
        manager.register("test_event", handler)

        manager.send_event("test_event", None)

        handler.assert_called_once_with(None)

    def test_send_event_async_handler(self, manager):
        """测试发送事件给异步处理器"""
        async_handler = AsyncMock()
        manager.register("test_event", async_handler)

        manager.send_event("test_event", {"async": True})

        # 异步处理器应该被调用
        async_handler.assert_called_once()

    # ==================== emit 测试 ====================

    def test_emit_alias(self, manager):
        """测试 emit 是 send_event 的别名"""
        handler = MagicMock()
        manager.register("test_event", handler)

        manager.emit("test_event", {"emit": True})

        handler.assert_called_once()

    # ==================== put_message 测试 ====================

    def test_put_message(self, manager):
        """测试发送消息通知"""
        handler = MagicMock()
        manager.register(EventType.MessageChannelWeb, handler)

        manager.put_message("telegram", "Test Title", "Test Content", user_id=123)

        handler.assert_called_once()
        call_data = handler.call_args[0][0]
        assert call_data["channel"] == "telegram"
        assert call_data["title"] == "Test Title"
        assert call_data["content"] == "Test Content"
        assert call_data["user_id"] == 123

    # ==================== 全局实例测试 ====================

    def test_global_event_bus(self):
        """测试全局事件管理器实例"""
        assert event_bus is not None
        assert isinstance(event_bus, EventManager)
