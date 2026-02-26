"""
Alembic 环境配置
用于数据库迁移
"""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool

from app.core.config import settings
from app.db.models import Base

# Alembic Config 对象
config = context.config

# 设置数据库 URL
config.set_main_option("sqlalchemy.url", settings.database_url)

# 解释日志配置文件
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置 target_metadata 用于 autogenerate 支持
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    离线模式运行迁移
    配置数据库 URL 但不连接数据库
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """执行迁移"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """异步运行迁移"""
    from sqlalchemy.ext.asyncio import async_engine_from_config

    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.database_url

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    在线模式运行迁移
    连接数据库并执行迁移
    """
    import asyncio
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
