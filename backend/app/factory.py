"""
FastAPI 应用工厂
创建和配置 FastAPI 应用
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.core.log import logger
from app.core.event import EventManager
from app.core.module import ModuleManager
from app.core.plugin import PluginManager
from app.core.cache import AsyncFileCache
from app.db import db_manager, Base
from app.tasks.download_monitor import DownloadMonitorTask


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    Args:
        app: FastAPI 应用
    """
    # 启动
    logger.info("MusicPilot 启动中...")

    # 确保必要目录存在
    settings.ensure_dirs()

    # 初始化数据库
    db_manager.init_db()
    await db_manager.create_tables()

    # 初始化核心组件
    app.state.event_manager = EventManager()
    app.state.module_manager = ModuleManager()
    app.state.cache = AsyncFileCache(settings.cache_path, settings.cache_ttl)

    # 初始化插件管理器
    plugin_manager = PluginManager(app.state.event_manager)
    app.state.plugin_manager = plugin_manager

    # 加载插件（从 app/plugins 目录）
    plugin_dir = Path(__file__).parent.parent / "plugins"
    if plugin_dir.exists():
        plugin_manager.load_plugins_from_dir(plugin_dir)

    # 加载模块（从配置）
    # TODO: 从数据库或配置文件加载模块配置
    module_configs = {}
    app.state.module_manager.load_modules(module_configs)

    # 启动插件
    for plugin in plugin_manager.get_running_plugins():
        plugin.enable()

    # 初始化定时任务调度器
    scheduler = AsyncIOScheduler()
    app.state.scheduler = scheduler

    # 启动下载监控任务
    download_monitor = DownloadMonitorTask(scheduler)
    download_monitor.start(interval=60)  # 每 60 秒检查一次
    app.state.download_monitor = download_monitor

    # 启动调度器
    scheduler.start()

    logger.info("MusicPilot 启动完成")

    yield

    # 关闭
    logger.info("MusicPilot 关闭中...")

    # 停止下载监控任务
    if hasattr(app.state, "download_monitor"):
        app.state.download_monitor.stop()

    # 停止调度器
    if hasattr(app.state, "scheduler"):
        app.state.scheduler.shutdown()

    # 停止所有模块
    app.state.module_manager.stop_all()

    # 关闭数据库连接
    await db_manager.close()

    logger.info("MusicPilot 关闭完成")


def create_app() -> FastAPI:
    """
    创建 FastAPI 应用

    Returns:
        FastAPI 应用实例
    """
    app = FastAPI(
        title="MusicPilot",
        description="A powerful music management system",
        version="0.1.0",
        docs_url="/docs" if settings.api_docs_enabled else None,
        redoc_url="/redoc" if settings.api_docs_enabled else None,
        lifespan=lifespan,
    )

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应该限制
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 全局异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"未处理的异常: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "服务器内部错误",
                "detail": str(exc) if settings.app_debug else None,
            }
        )

    # 健康检查端点
    @app.get("/health")
    async def health_check():
        """健康检查"""
        return {
            "status": "ok",
            "version": "0.1.0",
        }

    # 注册路由
    _register_routes(app)

    # 静态文件服务（媒体目录）
    if settings.media_path.exists():
        app.mount("/media", StaticFiles(directory=str(settings.media_path)), name="media")

    return app


def _register_routes(app: FastAPI):
    """
    注册路由

    Args:
        app: FastAPI 应用
    """
    # TODO: 注册 API 路由
    from app.api.apiv1 import api_router
    app.include_router(api_router, prefix=settings.api_v1_prefix)