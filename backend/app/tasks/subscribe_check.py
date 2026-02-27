"""
订阅检查定时任务
定期检查所有订阅，发现新内容并自动下载
"""


from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.chain.subscribe import SubscribeChain
from app.core.log import logger


class SubscribeCheckTask:
    """
    订阅检查定时任务
    """

    def __init__(self, scheduler: AsyncIOScheduler):
        self.scheduler = scheduler
        self.subscribe_chain = SubscribeChain()

    async def check_subscriptions(self):
        """
        检查所有订阅

        定期检查所有启用的订阅，发现新内容
        """
        logger.info("开始检查所有订阅")

        try:
            # 调用 SubscribeChain 检查所有订阅
            stats = await self.subscribe_chain.check_all()

            logger.info(
                f"订阅检查完成: "
                f"总数={stats['total']}, "
                f"处理={stats['processed']}, "
                f"新内容={stats['new_content']}, "
                f"错误={stats['errors']}"
            )

        except Exception as e:
            logger.error(f"订阅检查失败: {e}")

    def setup(self, interval_minutes: int = 60):
        """
        设置定时任务

        Args:
            interval_minutes: 检查间隔（分钟），默认 60 分钟
        """
        self.scheduler.add_job(
            self.check_subscriptions,
            "interval",
            minutes=interval_minutes,
            id="subscribe_check",
            name="订阅检查任务",
            replace_existing=True,
        )

        logger.info(f"订阅检查定时任务已设置，每 {interval_minutes} 分钟执行一次")

    async def run_once(self):
        """
        手动执行一次检查
        """
        await self.check_subscriptions()
