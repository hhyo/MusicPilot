# Packaging Boundary

本文件用于明确 `plugin_runtime/plugins/musicpilot/` 的边界：

- `static/`：接收 `frontend/dist/` 的构建产物。
- `api/`、`services/`、`models/` 等目录：接收 `backend/app/` 中对应源码或占位模块。
- `manifest/`：仅放置占位元数据，不伪造真实宿主 schema。
- `__init__.py`：仅保留插件最小元信息，不提前声明不存在的宿主入口。

Phase 0 TODO：

1. 等宿主插件安装契约明确后，再收敛真实 manifest 字段。
2. 等宿主后端挂载方式明确后，再确定 `main.py`/路由入口在运行时的最终位置。
3. 等发布策略进入后续阶段后，再补 zip / release 产物装配细节。

