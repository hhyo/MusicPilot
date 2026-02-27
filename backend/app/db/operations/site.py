"""
Site 操作类
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.site import Site
from app.db import OperBase


class SiteOper(OperBase[Site]):
    """Site 操作类"""

    async def get_enabled(self) -> List[Site]:
        """
        获取所有启用的站点

        Returns:
            站点列表
        """
        async with self.db_manager.get_session() as session:
            query = select(Site).where(Site.enabled == True).order_by(Site.priority.desc())
            result = await session.execute(query)
            return result.scalars().all()

    async def get_by_downloader(self, downloader: str) -> List[Site]:
        """
        根据下载器获取站点

        Args:
            downloader: 下载器类型

        Returns:
            站点列表
        """
        async with self.db_manager.get_session() as session:
            query = (
                select(Site)
                .where(Site.downloader == downloader, Site.enabled == True)
                .order_by(Site.priority.desc())
            )
            result = await session.execute(query)
            return result.scalars().all()

    async def get_by_priority(self, min_priority: int = None) -> List[Site]:
        """
        根据优先级获取站点

        Args:
            min_priority: 最小优先级

        Returns:
            站点列表
        """
        async with self.db_manager.get_session() as session:
            query = select(Site).where(Site.enabled == True)

            if min_priority is not None:
                query = query.where(Site.priority >= min_priority)

            query = query.order_by(Site.priority.desc())
            result = await session.execute(query)
            return result.scalars().all()

    async def toggle_enabled(self, id: int) -> Optional[Site]:
        """
        切换站点启用状态

        Args:
            id: 站点 ID

        Returns:
            更新后的站点对象
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(select(Site).where(Site.id == id))
            site = result.scalar_one_or_none()
            if not site:
                return None

            site.enabled = not site.enabled
            await session.commit()
            await session.refresh(site)
            return site

    async def test_connection(self, id: int) -> tuple[bool, str]:
        """
        测试站点连接

        Args:
            id: 站点 ID

        Returns:
            (是否成功, 消息)
        """
        site = await self.get_by_id(id)
        if not site:
            return False, "站点不存在"

        # TODO: 实现实际的连接测试
        # 这里需要调用站点模块的 test() 方法
        return True, "连接成功"
