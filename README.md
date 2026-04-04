# MusicPilot

MusicPilot 是一个参考 MoviePilot 插件体系思路构建的音乐能力扩展工程。当前仓库已完成 Phase 0 到 Phase 9 的 MVP 收口，并在本轮进一步把实现收缩为“接口语义明确、场景调用明确、数据来源明确”的形态。仓库继续保留已经验证过的真实宿主链路，但不再扩展通用策略、推荐或矩阵决策层。

## 项目简介

- `frontend/`：基于 Vue 3 + TypeScript + Vite 的独立前端壳，当前提供首页工作台、metadata 搜索页、榜单页、订阅页，以及从 metadata / chart item 创建订阅、执行一次 run、查看 organize backend / status / handoff 的最小前端闭环。
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
- Host search：当前保留 `mock + host-backed selectable`，但真实运行时按固定接口语义工作。`/api/v1/search/title` 与 `/api/v1/search/media/{mediaid}` 是两个不同语义，不再互相伪装成 fallback。
- Dispatch：当前保留 `mock + host-backed selectable`。当存在可靠 `media_in` 时走 `/api/v1/download/`；只有 `torrent_in` 时走 `/api/v1/download/add`。这两个接口是不同语义，不再由运行时策略层互相切换。
- Organize：当前保留 `mock + host-backed selectable` 的 preview/apply 双阶段边界。`preview` 已切换为 MusicPilot 本地音乐路径预览；`apply` 当前通过宿主底层 file/storage transfer runtime 执行音乐文件整理。音乐 metadata 恢复当前优先使用显式 `MetadataDetail`，其次使用已有上下文、嵌入音频标签与 `source_path` 线索。`history/download` 是新派发后的主 handoff 来源，`history/transfer` 只用于历史重放/补充来源，不再作为自动业务回退引擎。

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
export MUSICPILOT_HOST_HISTORY_SYNC_RETRY_ATTEMPTS=3
export MUSICPILOT_HOST_HISTORY_SYNC_RETRY_INTERVAL_SECONDS=1
export MUSICPILOT_HOST_HANDOFF_PENDING_TTL_SECONDS=120
export MUSICPILOT_HOST_TRANSFER_NAME_PATH=/api/v1/transfer/name
export MUSICPILOT_HOST_TRANSFER_QUEUE_PATH=/api/v1/transfer/queue
export MUSICPILOT_HOST_TRANSFER_NOW_PATH=/api/v1/transfer/now
export MUSICPILOT_HOST_SEARCH_MODE=prefer_host
export MUSICPILOT_HOST_DISPATCH_MODE=prefer_host
export MUSICPILOT_HOST_ORGANIZE_MODE=prefer_host
export MUSICPILOT_HOST_VALIDATION_MATRIX_PATH=/Users/me/path/to/MusicPilot/backend/data/host_validation_matrix.latest.json
```

可选模式：

- `mock`：始终使用 mock adapter
- `prefer_host`：优先使用 host-backed adapter；若 capability 不满足或运行时报错，直接暴露失败
- `strict_host`：必须使用 host-backed；能力不足时直接报错

## 当前固定调用规则

- metadata 搜索默认走 `/api/v1/search/title`；只有拿到可靠宿主媒体 ID 时才走 `/api/v1/search/media/{mediaid}`。
- candidate 派发时，有 `media_in` 就调用 `/api/v1/download/`；只有 `torrent_in` 时调用 `/api/v1/download/add`。
- dispatch 成功后的 `source_path` 主来源是 `/api/v1/history/download`。
- 历史重放或补充查询时，`source_path` 补充来源才是 `/api/v1/history/transfer`。
- organize preview 只走 MusicPilot 本地音乐路径预览。
- organize apply 只走宿主底层 file/storage transfer runtime。

这意味着当前系统不再做运行时路径计算：

- 一个场景对应一个确定调用语义
- 一个关键字段对应一个权威来源
- 失败就是失败，不再偷偷切到其他业务接口
- 验证矩阵只保留为验证产物，不再作为运行时决策器

## Breaking Cleanup 后的数据库处理

Phase 10 起，旧的 `backend/data/musicpilot.db` 不再兼容当前模型结构。升级后请直接重建：

```bash
cd backend
python -m app.db_init --rebuild
```

本仓库还提供本地验证 stub：

```bash
python3 scripts/host_integration_stub.py
```

它只用于验证 mock / host 适配器边界与 payload 语义，不代表真实 MoviePilot 宿主已经联通。

更细的真实宿主联调与历史验证结论见：

- [docs/08_Phase5_宿主接入联调说明.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/08_Phase5_宿主接入联调说明.md)
- [docs/09_Phase6_organize_联调说明.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/09_Phase6_organize_联调说明.md)
- [docs/10_Phase7A_真实宿主语义验证与差异收敛.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/10_Phase7A_真实宿主语义验证与差异收敛.md)
- [docs/11_Phase7B_真实成功样例闭环.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/11_Phase7B_真实成功样例闭环.md)
- [docs/12_Phase8_真实成功率验证矩阵.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/12_Phase8_真实成功率验证矩阵.md)
- [docs/14_架构收缩与语义归一说明.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/14_架构收缩与语义归一说明.md)
- [docs/15_彻底清理变更说明.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/15_%E5%BD%BB%E5%BA%95%E6%B8%85%E7%90%86%E5%8F%98%E6%9B%B4%E8%AF%B4%E6%98%8E.md)

## 如何复跑 Phase 8 成功样例矩阵

在本地私有环境准备好真实宿主 Base URL 和 token 后，可以手动执行：

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot
backend/.venv/bin/python scripts/run_phase8_real_host_matrix.py --allow-side-effects
```

建议输出到默认矩阵文件：

```bash
backend/.venv/bin/python scripts/run_phase8_real_host_matrix.py \
  --allow-side-effects \
  --output backend/data/host_validation_matrix.latest.json
```

它不会默认纳入自动测试；目的是让维护者在需要时手动验证：

- 哪些组合已经是 `stable`
- 哪些组合只有 `single_sample`
- 哪些组合被真实宿主明确阻断为 `blocked`

## 如何查看当前 active adapter

- `/health`：查看 `data.host_integration.active_search_adapter`、`active_dispatch_adapter` 和 `active_organize_adapter`
- `/health`：查看 `data.validation_matrix`
- `/api/probe/health`：查看 `data.runtime_state`
- `/api/probe/validation-matrix`：查看最新真实宿主验证矩阵
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
- Phase 8 / 真实成功率扩展与稳定性收敛
- Phase 9 / 基于真实成功率矩阵的策略收敛与可交付化
- 架构收缩与语义归一 / 固定调用规则、单一权威数据来源、去策略化收口
- 宿主能力探针 API 骨架
- MVP 路由骨架与统一响应结构
- metadata 搜索服务最小可用版
- SQLite 最小落库与本地 seed
- 前端搜索页最小闭环与详情视图
- QueryBuilder、SearchJob、候选评分与 mock dispatch 最小闭环
- 订阅模型与 API、mock charts/discovery、subscription run 记录与 host-aware organize preview/apply
- host-aware search / dispatch / organize adapter resolver、必要的 mock/real 环境切换与联调说明
- 真实 MoviePilot search / download / transfer 语义验证与字段映射收敛
- 真实宿主插件 API 下的音乐 `preview_ready -> applied` 最小闭环
- 真实宿主验证矩阵、多样例稳定性分类与手动回归脚本
- 验证矩阵作为验证产物保留，但不再驱动运行时策略决策

## 当前阶段未完成范围

- 真实榜单拉取与增量监控
- 真实第三方 metadata provider 接入
- 生产级订阅调度器与重试编排
- 真实 PT 搜索、匹配、下载派发
- 真实 organize 文件处理增强、音频标签解析与媒体库刷新
- 真实 MoviePilot 宿主安装与挂载逻辑
- 真实 MoviePilot `download/add` 多样例稳定成功
- 真实 MoviePilot `download_media` 到 organize 的稳定成功映射
- 下载完成后的生产级自动整理、刮削与媒体库刷新

以上能力本轮均只保留目录、接口、注释或说明性占位，不提前实现。

## 推荐演示路径

1. 先访问 `/health` 与 `/api/probe/validation-matrix`，确认当前 active adapter、verification state 和最新验证产物摘要。
2. 优先演示真实音乐样本下的 `preview_ready -> applied` organize 闭环。
3. 如需演示从搜索到派发，再补一条历史宿主验证路径，并明确那是早期影视语义验证记录，不代表当前音乐 organize 主实现。

更完整的说明见 [docs/13_Phase9_策略收敛与交付说明.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/13_Phase9_策略收敛与交付说明.md) 与 [docs/14_架构收缩与语义归一说明.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/14_架构收缩与语义归一说明.md)。

## 下一阶段建议推进方式

1. 在保留现有 response envelope 的前提下，继续增强 MusicPilot 自己的音乐 metadata 恢复能力，优先补本地标签解析与更稳定的目录/文件名恢复。
2. 引入真实 metadata provider adapter，让 metadata/search 不再停留在 seed/mock 层。
3. 在当前 SubscriptionExecutionService 骨架上补完整调度、重试、下载完成回调与 organize job 状态机。
4. 保持 `plugin_runtime/` 只作为构建产物边界，不把开发源码和宿主产物混放。
