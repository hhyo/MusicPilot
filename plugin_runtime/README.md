# plugin_runtime

`plugin_runtime/` 是 MusicPilot 面向未来 MoviePilot 宿主集成的运行时占位目录，不是开发源码目录。

Phase 0 当前职责：

- 提供插件产物目录模板
- 提供 manifest / metadata 占位
- 提供静态资源目录占位
- 提供后端挂载入口说明
- 作为 `scripts/package_plugin.py` 的目标装配目录

当前明确不做：

- 不伪造真实 MoviePilot 安装格式
- 不伪造真实宿主注册 API
- 不伪造真实插件入口函数

后续当宿主接口明确后，应在此目录上继续收敛为真实可交付插件产物，而不是把 `frontend/`、`backend/` 原样暴露给宿主。

