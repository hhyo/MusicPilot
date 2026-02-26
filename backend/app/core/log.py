"""
日志模块
使用 loguru 实现日志记录
"""
import sys
from pathlib import Path
from loguru import logger

from app.core.config import settings


class LogConfig:
    """日志配置类"""

    def __init__(self):
        self._initialized = False

    def init_logger(self):
        """初始化日志配置"""
        if self._initialized:
            return

        # 移除默认处理器
        logger.remove()

        # 确保日志目录存在
        log_dir = settings.log_path
        log_dir.mkdir(parents=True, exist_ok=True)

        # 控制台输出
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=settings.log_level,
            colorize=True,
        )

        # 文件输出（所有日志）
        logger.add(
            log_dir / "musicpilot_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation="00:00",  # 每天午夜轮转
            retention="30 days",  # 保留 30 天
            compression="zip",  # 压缩旧日志
            encoding="utf-8",
        )

        # 文件输出（错误日志）
        logger.add(
            log_dir / "musicpilot_error_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="ERROR",
            rotation="00:00",
            retention="90 days",
            compression="zip",
            encoding="utf-8",
        )

        self._initialized = True
        logger.info("日志系统初始化完成")


# 初始化日志配置
log_config = LogConfig()
log_config.init_logger()

# 导出 logger 实例
__all__ = ["logger"]
