"""MusicPilot runtime-capable package.

用途：
- 作为本地 FastAPI 工程的包根
- 作为 plugin_runtime 装配后的插件包根
- 保留最小版本号和插件元信息

注意：
- Phase 0 不实现真实 MoviePilot 插件注册逻辑
- Phase 0 不声明不存在的宿主 API
- 后续仅在宿主契约明确后补真实入口与注册信息
"""

__version__ = "0.1.0"
PLUGIN_NAME = "MusicPilot"
PLUGIN_DESCRIPTION = "Phase 0 runtime placeholder for future MoviePilot integration."
