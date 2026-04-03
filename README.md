# MusicPilot

MusicPilot 是一个参考 MoviePilot 插件体系思路构建的音乐能力扩展工程。当前仓库已完成 Phase 0、Phase 1、Phase 2、Phase 3、Phase 4、Phase 5、Phase 6、Phase 7A 与 Phase 7B，重点先交付可启动、可构建、可装配、可联调的工程骨架，以及从 metadata 到 QueryBuilder、SearchJob、候选评分、mock dispatch，再到 subscriptions、mock chart discovery、subscription run、host-aware organize preview/apply，并在 Phase 7B 收口到“真实 MoviePilot 宿主至少一条成功下载与 organize 闭环样例已可回看、可验证、可降级、可解释”的层级，而不是提前实现生产级自动化。

## 项目简介

- `frontend/`：基于 Vue 3 + TypeScript + Vite 的独立前端壳，当前提供首页工作台、metadata 搜索页、榜单页、订阅页，以及从 metadata / chart item 创建订阅、执行一次 run、查看 organize backend / status / fallback 的最小前端闭环。
- `backend/`：基于 FastAPI 的后端工程，当前提供统一响应结构、宿主探针骨架、metadata 搜索 API、SQLite 最小落库、QueryBuilder、SearchJob、评分、host-aware search/dispatch resolver、SubscriptionService、mock chart discovery 与 host-aware organize preview/apply boundary。
- `plugin_runtime/`：面向未来 MoviePilot 宿主集成的运行时占位产物目录，当前只保留 manifest、静态资源、后端挂载说明和打包边界。
- `scripts/`：前端开发、后端开发、前端构建、插件装配、版本同步脚本。
- `docs/`：产品方案、架构方案、规范与任务拆解文档，按要求保持原位不变。

## 仓库结构

```text
MusicPilot/
  frontend/
  backend/
  docs/
  scripts/
  plugin_runtime/
  README.md
  .gitignore
  .editorconfig
  .env.example
```

## 本地开发启动方式

前端：

```bash
cd frontend
pnpm install
pnpm dev
```

也可以直接运行：

```bash
./scripts/dev_frontend.sh
```

后端：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.db_init --reseed
uvicorn app.main:app --reload
```

也可以直接运行：

```bash
./scripts/dev_backend.sh
```

## 前后端构建方式

前端构建：

```bash
./scripts/build_frontend.sh
```

后端当前为源码运行形态，不提供 wheel 或容器产物，只保证：

- `uvicorn app.main:app --reload` 可启动
- `GET /health` 返回 200
- metadata search / detail API 可访问
- QueryBuilder / SearchJob / candidate / dispatch host-aware API 可访问
- subscriptions / charts / organize preview/apply API 可访问

## 数据初始化与 seed

Phase 6 继续采用最小可运行方案：`SQLite + SQLAlchemy + local seed metadata + mock/host-aware acquisition + mock chart data + mock/host-aware organize data`。

- 默认数据库文件：`backend/data/musicpilot.db`
- 手动初始化或重置 seed：

```bash
cd backend
python -m app.db_init --reseed
```

- 正常启动后端时也会自动建表，并在库为空时导入本地 seed
- 当前 seed 只用于验证 Artist / Album / Track 搜索链路、mock chart entry 和 subscription run 输入，不代表已经真实接入第三方音乐源或真实榜单源

## 当前执行模式与宿主集成边界

- Subscription 执行模式：当前仅支持手动触发一次同步 run，不启用生产级 cron、消息队列或分布式 scheduler。
- Chart discovery：当前为 local seed / mock chart source，只验证发现入口与从 chart item 创建订阅的动作。
- Host search：当前已升级为 `mock + host-backed selectable`。真实 MoviePilot `/api/v1/search/title` 与 `/api/v1/search/last` 已完成语义验证；`search/media` 仍待正向样例补充。
- Dispatch：当前已升级为 `mock + host-backed selectable`。Phase 7B 已对真实 `/api/v1/download/` 拿到 `success=true` 样例，并通过 `/api/v1/history/download` 回读本地路径；`download/add` 单独成功样例仍是 `unverified`。
- Organize：当前已升级为 `mock + host-backed selectable` 的 preview/apply 双阶段边界。Phase 7B 已把它映射到真实 MoviePilot `transfer/name` / `transfer/manual` 并拿到正向成功样例，同时把 `path_handoff` 写回 MusicPilot organize 链路。

## 如何启用 host integration

默认情况下，MusicPilot 会安全地停留在 mock adapter。要切到 host-aware 模式，可配置：

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
export MUSICPILOT_HOST_TRANSFER_NAME_PATH=/api/v1/transfer/name
export MUSICPILOT_HOST_TRANSFER_QUEUE_PATH=/api/v1/transfer/queue
export MUSICPILOT_HOST_TRANSFER_MANUAL_PATH=/api/v1/transfer/manual
export MUSICPILOT_HOST_TRANSFER_NOW_PATH=/api/v1/transfer/now
export MUSICPILOT_HOST_SEARCH_STRATEGY=prefer_host
export MUSICPILOT_HOST_DISPATCH_STRATEGY=prefer_host
export MUSICPILOT_HOST_ORGANIZE_STRATEGY=prefer_host
export MUSICPILOT_HOST_FALLBACK_TO_MOCK=true
```

可选策略：

- `mock`：始终使用 mock adapter
- `prefer_host`：优先 host-backed，失败时按配置回退 mock
- `strict_host`：必须使用 host-backed；能力不足时直接报错

本仓库还提供本地验证 stub：

```bash
python3 scripts/host_integration_stub.py
```

它只用于验证 resolver、payload 和 fallback，不代表真实 MoviePilot 宿主已经联通。

更细的真实宿主联调结论见：

- [docs/08_Phase5_宿主接入联调说明.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/08_Phase5_宿主接入联调说明.md)
- [docs/09_Phase6_organize_联调说明.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/09_Phase6_organize_联调说明.md)
- [docs/10_Phase7A_真实宿主语义验证与差异收敛.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/10_Phase7A_真实宿主语义验证与差异收敛.md)
- [docs/11_Phase7B_真实成功样例闭环.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/11_Phase7B_真实成功样例闭环.md)

## 如何查看当前 active adapter

- `/health`：查看 `data.host_integration.active_search_adapter`、`active_dispatch_adapter` 和 `active_organize_adapter`
- `/api/probe/health`：查看 `data.runtime_state`
- `/api/v1/plugin/musicpilot/jobs/{id}` 与 `/results`：查看 `adapter_resolution`
- `/api/v1/plugin/musicpilot/downloads/dispatch`：查看 `dispatch_backend`、`fallback_reason`
- `/api/v1/plugin/musicpilot/downloads/dispatch`：查看 `host_response_summary` 与 `path_handoff`
- `/api/v1/plugin/musicpilot/organize/preview`、`/apply` 与 `/organize/jobs/{id}`：查看 `organize_backend`、`organize_status`、`verification_state`、`fallback_reason` 与 `path_handoff`

## plugin_runtime 打包说明

Phase 0 的 `plugin_runtime/` 仍是占位运行时目录，不伪造真实 MoviePilot 宿主安装逻辑。当前提供的打包链路负责：

1. 将 `frontend/dist/` 装配到 `plugin_runtime/plugins/musicpilot/static/`
2. 将 `backend/app/` 装配到 `plugin_runtime/plugins/musicpilot/`
3. 将 `backend/requirements.txt` 同步到 `plugin_runtime/plugins/musicpilot/requirements.txt`
4. 保留 `manifest/` 与边界说明文件，供后续真实接入宿主时继续收敛

执行命令：

```bash
./scripts/package_plugin.sh
```

## 当前阶段完成范围

- Phase 0 / T01-T04
- Phase 1 / T05-T07
- Phase 2 / T08-T10
- Phase 3 / T11-T14
- Phase 4 / 订阅与编排最小闭环
- Phase 5 / 宿主真实接入优先级最高的收口阶段
- Phase 6 / 真实 organize 接入优先阶段
- Phase 7A / 真实 MoviePilot 宿主语义验证与差异收敛
- Phase 7B / 真实成功样例闭环打通
- 宿主能力探针 API 骨架
- MVP 路由骨架与统一响应结构
- metadata 搜索服务最小可用版
- SQLite 最小落库与本地 seed
- 前端搜索页最小闭环与详情视图
- QueryBuilder、SearchJob、候选评分与 mock dispatch 最小闭环
- 订阅模型与 API、mock charts/discovery、subscription run 记录与 host-aware organize preview/apply
- host-aware search / dispatch / organize adapter resolver、配置映射、fallback 机制与联调说明
- 真实 MoviePilot search / download / transfer 语义验证与字段映射收敛
- 真实 download success -> history path handoff -> transfer/name -> transfer/manual 的最小成功闭环

## 当前阶段未完成范围

- 真实榜单拉取与增量监控
- 真实第三方 metadata provider 接入
- 生产级订阅调度器与重试编排
- 真实 PT 搜索、匹配、下载派发
- 真实 organize 文件处理、标签、媒体库刷新
- 真实 MoviePilot 宿主安装与挂载逻辑
- 真实 MoviePilot `download/add` 单独成功样例
- 真实 MoviePilot `search/media` 正向样例
- 下载完成后的生产级自动整理、刮削与媒体库刷新

以上能力本轮均只保留目录、接口、注释或说明性占位，不提前实现。

## 下一阶段建议推进方式

1. 在保留现有 response envelope 的前提下，引入真实 metadata provider adapter。
2. 在当前已验证的真实成功样例基础上，继续补 `search/media`、`download/add` 和更丰富的 download history / transfer history 样例。
3. 在当前 SubscriptionExecutionService 骨架上补完整调度、重试、下载完成回调与 organize job 状态机。
4. 保持 `plugin_runtime/` 只作为构建产物边界，不把开发源码和宿主产物混放。
