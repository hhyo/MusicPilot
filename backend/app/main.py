"""
MusicPilot 主入口
"""

import uvicorn

from app.core.config import settings
from app.factory import create_app

# 创建 FastAPI 应用
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.is_dev,
        log_level=settings.log_level.lower(),
    )
