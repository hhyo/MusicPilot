# MusicPilot Backend

FastAPI 工程目录。当前已完成：

- 健康检查与统一响应结构
- 宿主能力探针 API 骨架
- metadata 搜索与详情最小闭环
- SQLite 最小落库与本地 seed 初始化
- QueryBuilder、SearchJob、候选评分与 mock dispatch 边界
- SubscriptionService、subscription run 与 mock chart discovery
- host-aware organize preview/apply 与 organize 状态记录
- host-aware search / dispatch / organize adapter resolver 与必要的 mock/real 环境切换
- 真实 MoviePilot search / download / transfer 语义收敛与差异记录
- 真实 download success -> history path handoff -> transfer/name -> transfer/manual 成功样例
- Phase 8 多样例真实验证矩阵与 path handoff 稳定性收敛
- 验证矩阵作为验证产物保留，运行时改回固定接口语义与固定调用规则

当前仍不包含：

- 真实第三方 metadata provider 接入
- 真实榜单抓取与增量监控
- 真实 PT 搜索与下载器派发
- 生产级订阅调度器与真实整理规则
- 真实 MoviePilot `download/add` 多样例稳定成功
- 生产级下载完成回调、自动整理与媒体库刷新

手动初始化本地数据库：

```bash
cd backend
python -m app.db_init --reseed
```

当前执行模式说明：

- `subscriptions/{id}/run` 为同步最小执行骨架
- `charts/*` 为 local seed / mock chart source
- `organize/preview` 和 `organize/apply` 会根据 host integration settings 在 mock 与 host-backed skeleton 间选择
- `jobs/*` 与 `downloads/dispatch` 会根据 host integration settings 在 mock 与 host-backed skeleton 间选择
- 当前真实运行时不再做 recommendation / strategy / matrix 驱动的路径决策；矩阵只保留为验证产物

启用 host integration 的最小配置示例：

```bash
export MUSICPILOT_HOST_INTEGRATION_ENABLED=true
export MUSICPILOT_HOST_BASE_URL=http://127.0.0.1:3000
export MUSICPILOT_HOST_AUTH_TOKEN="$TOKEN"
export MUSICPILOT_HOST_AUTH_MODE=x_api_key
export MUSICPILOT_HOST_API_KEY_HEADER_NAME=X-API-KEY
export MUSICPILOT_HOST_HEALTH_PATH=/api/v1/search/last
export MUSICPILOT_HOST_SITES_PATH=/api/v1/site
export MUSICPILOT_HOST_SEARCH_TITLE_PATH=/api/v1/search/title
export MUSICPILOT_HOST_SEARCH_MEDIA_PATH=/api/v1/search/media
export MUSICPILOT_HOST_SEARCH_LAST_PATH=/api/v1/search/last
export MUSICPILOT_HOST_DOWNLOADERS_PATH=/api/v1/download/clients
export MUSICPILOT_HOST_DOWNLOAD_ADD_PATH=/api/v1/download/add
export MUSICPILOT_HOST_DOWNLOAD_MEDIA_PATH=/api/v1/download/
export MUSICPILOT_HOST_HISTORY_DOWNLOAD_PATH=/api/v1/history/download
export MUSICPILOT_HOST_HISTORY_TRANSFER_PATH=/api/v1/history/transfer
export MUSICPILOT_HOST_HISTORY_SYNC_RETRY_ATTEMPTS=3
export MUSICPILOT_HOST_HISTORY_SYNC_RETRY_INTERVAL_SECONDS=1
export MUSICPILOT_HOST_HANDOFF_PENDING_TTL_SECONDS=120
export MUSICPILOT_HOST_TRANSFER_NAME_PATH=/api/v1/transfer/name
export MUSICPILOT_HOST_TRANSFER_QUEUE_PATH=/api/v1/transfer/queue
export MUSICPILOT_HOST_TRANSFER_MANUAL_PATH=/api/v1/transfer/manual
export MUSICPILOT_HOST_TRANSFER_NOW_PATH=/api/v1/transfer/now
export MUSICPILOT_HOST_SEARCH_STRATEGY=prefer_host
export MUSICPILOT_HOST_DISPATCH_STRATEGY=prefer_host
export MUSICPILOT_HOST_ORGANIZE_STRATEGY=prefer_host
export MUSICPILOT_HOST_VALIDATION_MATRIX_PATH=/Users/me/path/to/MusicPilot/backend/data/host_validation_matrix.latest.json
```

若没有真实宿主，可运行：

```bash
python3 ../scripts/host_integration_stub.py
```

然后通过 `/health`、`/api/probe/health`、`/api/probe/validation-matrix`、`/jobs/*`、`/downloads/dispatch` 与 `/organize/*` 查看当前 active adapter、backend、verification state、fallback、`path_handoff` 与多样例验证产物。更完整的联调说明见 [docs/08_Phase5_宿主接入联调说明.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/08_Phase5_宿主接入联调说明.md)、[docs/09_Phase6_organize_联调说明.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/09_Phase6_organize_联调说明.md)、[docs/10_Phase7A_真实宿主语义验证与差异收敛.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/10_Phase7A_真实宿主语义验证与差异收敛.md)、[docs/11_Phase7B_真实成功样例闭环.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/11_Phase7B_真实成功样例闭环.md)、[docs/12_Phase8_真实成功率验证矩阵.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/12_Phase8_真实成功率验证矩阵.md)、[docs/13_Phase9_策略收敛与交付说明.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/13_Phase9_策略收敛与交付说明.md) 和 [docs/14_架构收缩与语义归一说明.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/14_架构收缩与语义归一说明.md)。

当前建议这样理解当前路径：

- 历史重放/补充来源：`history/transfer -> organize replay/apply`
- 单样例真实链路：`search/title -> download_add -> history/download -> transfer/manual -> organize`
- 已知不应自动继续尝试的失败场景：`download_media + resolved_from_history_download -> organize apply`

手动回归真实宿主样例矩阵：

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot
backend/.venv/bin/python scripts/run_phase8_real_host_matrix.py --allow-side-effects
```

启动方式见仓库根目录 [README.md](../README.md)。
