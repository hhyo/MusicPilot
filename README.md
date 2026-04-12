# MusicPilot

MusicPilot 是一个参考 MoviePilot 插件体系思路构建的音乐能力扩展工程。当前仓库已经完成插件壳层、metadata 搜索、手动订阅执行，以及音乐 organize `preview -> apply` 的真实宿主最小闭环，并继续沿“接口语义明确、场景调用明确、数据来源明确”的方向推进，不再扩展通用策略、推荐或矩阵决策层。

统一音乐媒体解析链后端收口已经完成：`MusicMediaInput -> MusicMetaBase -> MusicMediaInfo` 现在是后端唯一的上层音乐识别主路径。这条链参考 MoviePilot 统一媒体解析链的设计方法，但保持音乐领域模型独立；当前已经接管 discovery 下钻 detail、search job 输入、query builder、candidate scoring、subscription execution 与 organize 上游识别。RSS / 弱来源榜单项会在创建订阅时直接固化 `MusicMediaInput`、`MusicMetaBase`、`MusicRecognitionAssessment` 与 `MusicMediaInfo` 显式快照，后续 run、organize 和 detail 都只复用这些正式字段；旧的 `DiscoveryTarget / resolution_hints / /metadata/lookup` 过渡桥接已经退出活跃后端主路径。

## 项目简介

- `frontend/`：基于 Vue 3 + TypeScript + Vite 的前端工程，当前已切换到 `Vuetify` 组件体系并按 MoviePilot 风格重建页面结构；既可作为独立开发页运行，也可通过宿主插件中心的 `vue` 远程组件模式加载。当前已提供首页工作台、Discovery 榜单页、Metadata 搜索页、订阅执行页、最小可用 `/settings` 设置页，以及真实可读写的 `/settings/providers` 接口页面；同时已新增宿主首页 dashboard 入口卡片，以及宿主侧边栏导航与独立页面入口，可从 MoviePilot 首页或侧栏快速打开 MusicPilot。前端支持从 metadata / chart entry 打开统一 detail、创建订阅、创建并执行 SearchJob、查看 run / candidate / organize 状态。
- `backend/`：基于 FastAPI 的后端工程，当前提供统一响应结构、宿主探针骨架、metadata 搜索 API、SQLite 最小落库、QueryBuilder、SearchJob、评分、search/dispatch 模式选择、SubscriptionService、真实 settings 读写接口、RSS / ListenBrainz chart discovery，以及音乐 organize preview/apply 最小闭环。
- `plugin_runtime/`：面向 MoviePilot 宿主的运行时装配目录，当前已完成本地宿主真实加载验证，并已通过宿主插件中心 `vue` 远程组件模式、首页 dashboard 远程组件，以及宿主侧边栏 `plugin-app` 独立页面入口打开 MusicPilot 页面。目录中保留静态资源、后端挂载说明和打包边界。
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

当前继续采用最小可运行方案：`SQLite + SQLAlchemy + seed 或 MusicBrainz metadata + local chart data + search/dispatch 模式选择 + 音乐 organize preview/apply`。

- 默认数据库文件：`backend/data/musicpilot.db`
- 手动初始化或重置 seed：

```bash
cd backend
python -m app.db_init --reseed
```

- 正常启动后端时也会自动建表，并在库为空时导入本地 seed
- 当前 seed 仍用于默认开发模式下的 Artist / Album / Track 搜索链路、chart entry 和 subscription run 输入；当切到 `musicbrainz` / `listenbrainz` 模式时，可分别使用真实 metadata 与真实榜单源

## 当前执行模式与宿主集成边界

- Metadata provider：当前支持 `seed` 与 `musicbrainz` 两种模式。`seed` 继续作为默认开发数据；`musicbrainz` 提供 Artist / Album / Track 的实时搜索与详情。当前 detail 已补齐最小结构化增强：album detail 会从最佳 release 读取真实 track listing，track detail 的 related album 会对齐到 release-group 语义，并带出可选的 `disambiguation` / `release_count` / `track_number` / `disc_number`。普通 keyword search 会按 MusicBrainz 官方 plain indexed search 方式带 `dismax=true`；recording detail 会直接请求 `release-groups`。album / track detail 会补充最佳 release 的发行上下文，例如 `status`、`country`、`barcode`、`label_names`、`media_format`、`track_count`、`disc_count` 和 `secondary_types`；artist detail 则会补 discovery 更关心的上下文，例如 `sort_name`、`artist_type`、`area_name`、`begin_area_name`、`ended`、`release_group_count`、`primary_release_types`，以及面向 discovery 的 `featured_albums / featured_singles / featured_other_releases` 分类摘要。
- Subscription 执行模式：当前支持手动触发一次同步 run，以及最小应用内 scheduler 自动触发 due subscription。执行链已能对最佳 `AUTO_DOWNLOAD` 候选自动 dispatch 并生成 organize preview；若 preview 已具备明确本地源文件，则会继续自动 apply。对于 `path_handoff.handoff_status=pending_history_sync` 的已派发 run，后台 scheduler 现在也会继续轮询宿主 download history：一旦回填到明确本地源路径，就会自动续跑 organize apply；若超过 `host_handoff_pending_ttl_seconds` 仍未命中，则会把 organize record 标记为 `failed`，并在 run 摘要中写入 `handoff_unresolved`。生产级 cron、消息队列、失败重试和分布式 scheduler 仍待后续补齐。
- Chart discovery：当前支持 `mock`、`listenbrainz` 与 `rss_feed` 三种模式。运行时会优先读取项目 settings 里的 chart provider 配置，环境变量仅作为 fallback。`listenbrainz` 第一版已接入 sitewide artists / recordings 榜单；`rss_feed` 已能通过 settings 配置真实进入 discovery，当前验证样本包括网易云热歌榜 playlist RSS、YouTube TopSongs RSS、YouTube TopArtists RSS，且 `item_count` 分别可写为 `200`、`100`、`100`。fresh install 时，`chart_rss_feeds` 还会带出 5 条内置默认源：网易云热歌榜、网易云新歌榜、网易云原创榜、YouTube 热门歌曲榜、YouTube 热门歌手榜。discovery 条目现在统一先进入 `MusicMediaInput -> MusicMetaBase -> MusicRecognitionAssessment` 准备阶段，再经 `/media/resolve/detail` 下钻正式 metadata detail；后端不再保留 `direct_id / search_lookup / resolution_hints` 这类旧桥接模式。对于 RSS / 弱来源 chart entry，创建订阅时会直接持久化统一链显式字段，run 阶段再统一按正式 `MusicMediaInfo` 继续 search / organize。当前 metadata provider 仍可能在 `seed` 模式下返回“未匹配到 metadata”，这属于当前运行态结果，不是 discovery 接口缺失。
- Host search：当前保留 `mock + host-backed selectable`，但真实运行时按固定接口语义工作。`/api/v1/search/title` 与 `/api/v1/search/media/{mediaid}` 是两个不同语义，不再互相伪装成 fallback。
- Dispatch：当前保留 `mock + host-backed selectable`。当存在可靠 `media_in` 时走 `/api/v1/download/`；只有 torrent 但已具备宿主媒体参考时走 `/api/v1/download/add`；音乐 torrent-only 候选则走宿主 downloader runtime 直接提交下载器。这几条路径是不同语义，不再由运行时策略层互相切换。
- Organize：当前保留 `mock + host-backed selectable` 的 preview/apply 双阶段边界。`preview` 已切换为 MusicPilot 本地音乐路径预览；`apply` 当前通过宿主底层 file/storage transfer runtime 执行音乐文件整理。音乐 metadata 识别当前优先使用显式 `MetadataDetail`，其次使用已有上下文、嵌入音频标签与 `source_path` 线索。`history/download` 是新派发后的主 handoff 来源，`history/transfer` 只用于历史重放/补充来源，不再作为自动业务回退引擎。

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

如需启用真实 metadata provider，可额外配置：

```bash
export MUSICPILOT_METADATA_PROVIDER_MODE=musicbrainz
export MUSICPILOT_METADATA_PROVIDER_TIMEOUT_SECONDS=15
export MUSICPILOT_METADATA_MUSICBRAINZ_BASE_URL=https://musicbrainz.org/ws/2
export MUSICPILOT_METADATA_PROVIDER_USER_AGENT='MusicPilot/0.1.0 (local)'
export MUSICPILOT_METADATA_CACHE_ENABLED=true
export MUSICPILOT_METADATA_CACHE_MAXSIZE=512
export MUSICPILOT_METADATA_SEARCH_CACHE_TTL_SECONDS=1800
export MUSICPILOT_METADATA_DETAIL_CACHE_TTL_SECONDS=21600
```

如需启用真实 chart provider，可额外配置：

```bash
export MUSICPILOT_CHART_PROVIDER_MODE=listenbrainz
export MUSICPILOT_CHART_PROVIDER_TIMEOUT_SECONDS=15
export MUSICPILOT_CHART_LISTENBRAINZ_BASE_URL=https://api.listenbrainz.org
export MUSICPILOT_CHART_PROVIDER_USER_AGENT='MusicPilot/0.1.0 (local)'
export MUSICPILOT_CHART_LISTENBRAINZ_RANGE=week
export MUSICPILOT_CHART_LISTENBRAINZ_COUNT=20
export MUSICPILOT_CHART_CACHE_ENABLED=true
export MUSICPILOT_CHART_CACHE_MAXSIZE=256
export MUSICPILOT_CHART_CACHE_TTL_SECONDS=900
export MUSICPILOT_SUBSCRIPTION_SCHEDULER_ENABLED=true
export MUSICPILOT_SUBSCRIPTION_SCHEDULER_POLL_SECONDS=30
export MUSICPILOT_SUBSCRIPTION_SCHEDULER_DEFAULT_INTERVAL_MINUTES=360
```

如需启用 RSS chart provider，可配置：

```bash
export MUSICPILOT_CHART_PROVIDER_MODE=rss_feed
export MUSICPILOT_CHART_RSS_FEEDS='[
  {"id":"netease-liked","label":"网易云喜欢","url":"https://rsshub.app/163/music/playlist/9345476","category":"liked","region":"CN","enabled":true},
  {"id":"youtube-top-artists-us","label":"YouTube Top Artists US","url":"https://rsshub.app/youtube/charts/TopArtists/us","category":"top-artists","region":"US","enabled":true}
]'
```

当前运行态里，RSS feeds 也可以通过 `/settings/providers` 真实读写，且保存后的 `chart_rss_feeds` 会直接进入 charts discovery。若没有项目设置与环境覆盖，fresh install 默认会带出上述 5 条内置 RSS feed。

可选模式：

- `mock`：始终使用 mock adapter
- `prefer_host`：优先使用 host-backed adapter；若 capability 不满足或运行时报错，直接暴露失败
- `strict_host`：必须使用 host-backed；能力不足时直接报错

当前 `metadata` 与 `charts` 的真实 provider 已支持最小缓存：

- 在真实插件运行态下，优先复用 MoviePilot 推荐的统一 `TTLCache`
- 在本地 backend/test 运行态下，自动回退到本地内存 TTL cache
- 第一阶段缓存面只覆盖 provider 输出，不包含后台刷新、复杂 RSS 可视化 CRUD 或持久化缓存管理

## 当前固定调用规则

- metadata 搜索默认走 `/api/v1/search/title`；只有拿到可靠宿主媒体 ID 时才走 `/api/v1/search/media/{mediaid}`。
- candidate 派发时，有 `media_in` 就调用 `/api/v1/download/`；只有 torrent 且已具备宿主媒体参考时调用 `/api/v1/download/add`；音乐 torrent-only 候选则调用宿主 downloader runtime。
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

`plugin_runtime/` 当前是面向 MoviePilot 的装配目录。当前提供的打包链路负责：

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
- 订阅模型与 API、本地 charts/discovery 入口、subscription run 记录与音乐 organize preview/apply
- `/settings` 最小可用设置页与 `/settings/providers` 真实读写接口
- RSS chart discovery 真正接入 settings 运行态，并已验证网易云热歌榜、YouTube TopSongs、YouTube TopArtists
- search / dispatch / organize 接入模式选择、必要的 mock/real 环境切换与联调说明
- 真实 MoviePilot search / download / transfer 语义验证与字段映射收敛
- 真实宿主插件 API 下的音乐 `preview_ready -> applied` 最小闭环
- 真实宿主验证矩阵、多样例稳定性分类与手动回归脚本
- 验证矩阵作为验证产物保留，但不再驱动运行时策略决策

## 当前阶段未完成范围

- 真实榜单拉取与增量监控
- 更多 metadata provider、provider 配置持久化与后台刷新
- 生产级订阅调度器与重试编排
- 真实 PT 搜索命中质量优化、更多站点覆盖与下载完成后自动整理
- 真实 organize 文件处理增强与媒体库刷新
- 真实 MoviePilot 宿主安装与挂载逻辑
- 基于宿主 downloader runtime 的更多真实下载样例、path handoff 稳定性与自动 organize 收口
- 真实 MoviePilot `download_media` 到 organize 的稳定成功映射
- 下载完成后的生产级自动整理、刮削与媒体库刷新
- 复杂 RSS 可视化 CRUD 与更多 discovery 产品化交互

以上能力本轮均只保留目录、接口、注释或说明性占位，不提前实现。

## 推荐演示路径

1. 先访问 `/health` 与 `/api/probe/validation-matrix`，确认当前 active adapter、verification state 和最新验证产物摘要。
2. 优先演示真实音乐样本下的 `preview_ready -> applied` organize 闭环。
3. 如需演示从搜索到派发，再补一条历史宿主验证路径，并明确那是早期影视语义验证记录，不代表当前音乐 organize 主实现。

更完整的说明见 [docs/13_Phase9_策略收敛与交付说明.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/13_Phase9_策略收敛与交付说明.md) 与 [docs/14_架构收缩与语义归一说明.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/14_架构收缩与语义归一说明.md)。

## 下一阶段建议推进方式

1. 在保留现有 response envelope 的前提下，继续增强 MusicPilot 自己的音乐 metadata 识别能力，优先补无标签文件的目录/文件名识别、多源 provider 与 provider 刷新策略。
2. 继续提升 discovery / search 的真实命中质量，让 ListenBrainz / MusicBrainz 入口更贴近当前 PT 环境可获取样本。
3. 在当前 SubscriptionExecutionService 骨架上补完整调度、重试、下载完成回调与 organize job 状态机。
4. 保持 `plugin_runtime/` 只作为构建产物边界，不把开发源码和宿主产物混放。
