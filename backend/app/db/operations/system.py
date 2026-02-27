"""
SystemConfig 操作类
"""

from typing import Optional, List
from sqlalchemy import select

from app.db.models.system import SystemConfig
from app.db import OperBase


class SystemConfigOper(OperBase[SystemConfig]):
    """SystemConfig 操作类"""

    async def get_by_key(self, key: str) -> Optional[SystemConfig]:
        """
        根据键获取配置

        Args:
            key: 配置键

        Returns:
            配置对象
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(select(SystemConfig).where(SystemConfig.key == key))
            return result.scalar_one_or_none()

    async def get_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        获取配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        config = await self.get_by_key(key)
        if config:
            return config.value
        return default

    async def set_value(self, key: str, value: str) -> SystemConfig:
        """
        设置配置值（存在则更新，不存在则创建）

        Args:
            key: 配置键
            value: 配置值

        Returns:
            配置对象
        """
        config = await self.get_by_key(key)
        if config:
            return await self.update(config.id, value=value)
        else:
            return await self.create(key=key, value=value)

    async def delete_by_key(self, key: str) -> bool:
        """
        根据键删除配置

        Args:
            key: 配置键

        Returns:
            是否删除成功
        """
        config = await self.get_by_key(key)
        if config:
            return await self.delete(config.id)
        return False

    async def get_all_configs(self) -> dict[str, str]:
        """
        获取所有配置

        Returns:
            配置字典
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(select(SystemConfig))
            configs = result.scalars().all()
            return {config.key: config.value for config in configs}

    async def batch_set(self, configs: dict[str, str]) -> List[SystemConfig]:
        """
        批量设置配置

        Args:
            configs: 配置字典

        Returns:
            配置对象列表
        """
        results = []
        for key, value in configs.items():
            config = await self.set_value(key, value)
            results.append(config)
        return results
