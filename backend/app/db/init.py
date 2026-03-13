"""
数据库初始化脚本
"""

from app.core.log import logger
from app.db import db_manager


async def init_database():
    """
    初始化数据库
    创建所有表
    """
    logger.info("开始初始化数据库...")

    # 初始化数据库连接
    db_manager.init_db()

    # 创建所有表
    await db_manager.create_tables()

    logger.info("数据库初始化完成")


async def drop_database():
    """
    删除所有表（慎用！）
    """
    logger.warning("开始删除数据库表...")

    # 删除所有表
    await db_manager.drop_tables()

    logger.warning("数据库表删除完成")


async def close_database():
    """
    关闭数据库连接
    """
    await db_manager.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(init_database())
