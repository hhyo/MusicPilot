# Scripts

Phase 0 提供的脚本：

- `dev_frontend.sh`：启动前端开发环境
- `dev_backend.sh`：启动后端开发环境
- `build_frontend.sh`：构建前端
- `package_plugin.sh`：构建前端并装配 `plugin_runtime/`
- `package_plugin.py`：执行实际装配逻辑
- `sync_version.py`：同步版本号到前端、后端与运行时占位产物
- `host_integration_stub.py`：本地宿主联调 stub，用于验证 host-preferred / strict / fallback 行为，尽量模拟 MoviePilot 的 `search / download / history / transfer` 语义
- `run_phase8_real_host_matrix.py`：手动触发真实宿主成功率验证矩阵，导出 `backend/data/host_validation_matrix.latest.json`

脚本目标是保证：

- 命令入口简单
- 装配边界清晰
- 可以继续演进到后续阶段，而不是一次性写死宿主实现

本地 stub 用法：

```bash
python3 scripts/host_integration_stub.py
```

默认监听 `http://127.0.0.1:19090`，仅用于验证 resolver、payload 和 fallback，不代表真实 MoviePilot 宿主。

Phase 8 真实宿主矩阵脚本用法：

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot
backend/.venv/bin/python scripts/run_phase8_real_host_matrix.py --allow-side-effects
```

说明：

- 它不是默认自动测试，不会在 `unittest` 或前端构建中自动跑。
- 需要本机私有环境里已经注入真实 MoviePilot Base URL 和 token。
- 默认输出文件是 `backend/data/host_validation_matrix.latest.json`。
- 目的是回看 `stable / single_sample / blocked / unverified` 这些真实样例状态，而不是单纯证明“曾经成功过一次”。
- Phase 9 开始，这份矩阵还会进一步驱动默认策略选择与 blocked 路径显式阻断。

Phase 7B 后，stub 与真实宿主仍有这些边界差异需要注意：

- stub 只是“语义逼近”，不能替代真实宿主样例
- stub 已模拟 `history/download` 与 `history/transfer`，可用于回归 `path_handoff`
- 真实宿主 `search/title`、`download/clients`、`download/`、`transfer/name`、`transfer/manual` 已在 docs 中记录到实测差异
- 真实宿主 `transfer/now` 需要 `?token=`，这一点已经被 stub 同步模拟

详细差异见 [docs/10_Phase7A_真实宿主语义验证与差异收敛.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/10_Phase7A_真实宿主语义验证与差异收敛.md)、[docs/11_Phase7B_真实成功样例闭环.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/11_Phase7B_真实成功样例闭环.md)、[docs/12_Phase8_真实成功率验证矩阵.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/12_Phase8_真实成功率验证矩阵.md) 和 [docs/13_Phase9_策略收敛与交付说明.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/13_Phase9_策略收敛与交付说明.md)。

Phase 9 交付建议：

- 演示前先查看 `/api/probe/validation-matrix`
- 优先展示 stable 的 `history/transfer` replay 路径
- 不要默认演示已知 blocked 的 `download_media + history/download -> organize apply`
