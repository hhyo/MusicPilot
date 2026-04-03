# Scripts

Phase 0 提供的脚本：

- `dev_frontend.sh`：启动前端开发环境
- `dev_backend.sh`：启动后端开发环境
- `build_frontend.sh`：构建前端
- `package_plugin.sh`：构建前端并装配 `plugin_runtime/`
- `package_plugin.py`：执行实际装配逻辑
- `sync_version.py`：同步版本号到前端、后端与运行时占位产物
- `host_integration_stub.py`：本地宿主联调 stub，用于验证 host-preferred / strict / fallback 行为，覆盖 search / dispatch / organize preview / organize apply

脚本目标是保证：

- 命令入口简单
- 装配边界清晰
- 可以继续演进到后续阶段，而不是一次性写死宿主实现

本地 stub 用法：

```bash
python3 scripts/host_integration_stub.py
```

默认监听 `http://127.0.0.1:19090`，仅用于验证 Phase 6 的 host-aware resolver，不代表真实 MoviePilot 宿主。
