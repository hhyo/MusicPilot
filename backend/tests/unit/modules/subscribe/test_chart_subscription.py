"""榜单订阅集成测试 - TDD"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest


class TestChartSubscription:
    """测试榜单订阅功能 - 使用 TDD 方式开发"""

    def test_subscription_type_enum_exists(self):
        """测试 SubscriptionType 枚举存在 🆕"""
        from app.modules.subscribe.models import SubscriptionType

        # 验证 CHART 类型存在
        assert hasattr(SubscriptionType, "CHART")
        assert SubscriptionType.CHART.value == "chart"

    def test_chart_source_enum_exists(self):
        """测试 ChartSource 枚举存在 🆕"""
        from app.modules.subscribe.models import ChartSource

        # 验证榜单数据源存在
        assert hasattr(ChartSource, "NETEASE")
        assert hasattr(ChartSource, "SPOTIFY")
        assert hasattr(ChartSource, "QQ_MUSIC")
        assert ChartSource.NETEASE.value == "netease"

    def test_subscription_model_chart_fields(self):
        """测试 Subscription 模型有榜单字段 🆕"""
        from app.modules.subscribe.models import ChartSource, Subscription, SubscriptionType

        sub = Subscription(
            type=SubscriptionType.CHART,
            name="网易云新歌榜",
            chart_source=ChartSource.NETEASE,
            chart_type="new_songs",
            chart_limit=50,
            auto_download=True,
        )

        assert sub.type == SubscriptionType.CHART
        assert sub.chart_source == ChartSource.NETEASE
        assert sub.chart_type == "new_songs"
        assert sub.chart_limit == 50
        assert sub.auto_download is True

    @pytest.mark.asyncio
    async def test_subscribe_module_exists(self):
        """测试 SubscribeModule 存在 🆕"""
        from app.modules.subscribe.subscribe_module import SubscribeModule

        module = SubscribeModule()
        assert module is not None
        assert hasattr(module, "process_chart_subscription")

    @pytest.mark.asyncio
    async def test_process_chart_subscription(self):
        """测试处理榜单订阅 🆕"""
        from app.modules.chart.fetchers.base import ChartData, ChartEntry
        from app.modules.subscribe.models import ChartSource, Subscription, SubscriptionType
        from app.modules.subscribe.subscribe_module import SubscribeModule

        # Mock ChartData
        mock_chart_data = ChartData(
            source="netease",
            chart_type="new_songs",
            updated_at=datetime.now(),
            entries=[ChartEntry(rank=1, title="Test Song", artist="Test Artist")],
        )

        # Patch at module level
        with patch(
            "app.modules.chart.chart_module.ChartModule.fetch_chart", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = mock_chart_data

            subscribe_module = SubscribeModule()

            # 创建榜单订阅
            subscription = Subscription(
                type=SubscriptionType.CHART,
                name="网易云新歌榜",
                chart_source=ChartSource.NETEASE,
                chart_type="new_songs",
                chart_limit=10,
                auto_download=False,
            )

            # 处理订阅 - 测试方法存在并可调用
            result = await subscribe_module.process_chart_subscription(subscription)

            # 验证 fetch_chart 被调用
            mock_fetch.assert_called_once()

            # 验证返回结果
            assert result is not None
            assert len(result) == 1
            assert result[0].title == "Test Song"

    @pytest.mark.asyncio
    async def test_chart_subscription_deduplication(self):
        """测试榜单订阅去重 🆕"""
        from app.modules.chart.fetchers.base import ChartEntry
        from app.modules.subscribe.subscribe_module import SubscribeModule

        subscribe_module = SubscribeModule()

        # 初始化去重缓存
        subscribe_module._downloaded_cache = {"Test Song-Test Artist"}

        # 创建包含重复歌曲的榜单数据
        entries = [
            ChartEntry(rank=1, title="Test Song", artist="Test Artist"),  # 重复
            ChartEntry(rank=2, title="New Song", artist="New Artist"),  # 新歌曲
        ]

        # 去重处理
        new_entries = subscribe_module._filter_duplicates(entries)

        assert len(new_entries) == 1
        assert new_entries[0].title == "New Song"

    @pytest.mark.asyncio
    async def test_chart_module_fetch_chart_method(self):
        """测试 ChartModule 有 fetch_chart 方法 🆕"""
        from app.modules.chart.chart_module import ChartModule

        module = ChartModule()
        assert hasattr(module, "fetch_chart")
        assert callable(module.fetch_chart)
