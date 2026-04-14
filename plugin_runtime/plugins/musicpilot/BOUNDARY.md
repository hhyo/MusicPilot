# Packaging Boundary

本文件用于明确 `plugin_runtime/plugins/musicpilot/` 的边界：

- `static/`：接收 `frontend/dist/` 的构建产物。
- `api/endpoints/`、`chain/`、`db/`、`helper/`、`modules/`、`core/`、`startup/`、`utils/`：与 `backend/app/` 保持同构镜像。
- `manifest/`：仅放置占位元数据，不伪造真实宿主 schema。
- `__init__.py`、`main.py`、`db_init.py`：与 `backend/app/` 保持同构镜像，只在插件打包边界补充宿主入口与静态资源。

Phase 0 TODO：

1. 等宿主插件安装契约明确后，再收敛真实 manifest 字段。
2. 等宿主后端挂载方式明确后，再确定 `main.py`/路由入口在运行时的最终位置。
3. 等发布策略进入后续阶段后，再补 zip / release 产物装配细节。
