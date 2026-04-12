# MusicPilot Backend

FastAPI 工程目录。当前已完成：

- 健康检查与统一响应结构
- 宿主能力探针 API 骨架
- metadata 搜索与详情最小闭环
- MusicBrainz Artist / Album / Track 搜索与详情最小接入，以及 detail 结构化增强
- SQLite 最小落库与本地 seed 初始化
- QueryBuilder、SearchJob、候选评分与 mock dispatch 边界
- SubscriptionService、subscription run、最小应用内 scheduler 与 mock/ListenBrainz chart discovery
- 音乐 organize preview/apply 与 organize 状态记录
- search / dispatch / organize 接入模式选择与必要的 mock/real 环境切换
- `/settings` 最小可用设置页与 `/settings/providers` 真实读写接口
- 宿主插件中心 `vue` 远程组件页面入口
- 宿主首页 dashboard `vue` 远程组件入口
- 宿主侧边栏导航与 `plugin-app` 独立页面入口
- 真实 MoviePilot search / downloader runtime / transfer 语义收敛与差异记录
- 真实宿主插件 API 下的音乐 `preview_ready -> applied` 成功样例
- Phase 8 多样例真实验证矩阵与 path handoff 稳定性收敛
- 验证矩阵作为验证产物保留，运行时改回固定接口语义与固定调用规则

当前也已经启动统一音乐媒体解析链重构：`MusicMediaInput -> MusicMetaBase -> MusicMediaInfo`。这条统一音乐媒体解析链参考 MoviePilot 的设计方法，但不复用影视模型本身；当前已经接管 discovery/detail 主路径，并继续进入 chart_entry 订阅创建、subscription execution、SearchJob、QueryBuilder、candidate scoring 与 organize 上游识别。discovery 侧的旧 `conversion_*` 表述已经退场，当前正式输出 `MusicMetaBase + recognition_state / recognition_note`。RSS / 弱来源 chart entry 现在会在创建订阅时先固化 `MusicMediaInput`、`MusicMetaBase` 与 `MusicMediaInfo` 相关快照，再进入后续 run；SearchJob 也已改为持久化统一输入与正式媒体对象，不再依赖旧的 `metadata_snapshot / query_source_type / query_source_id`。后续仍需继续把更多下游场景完全收口到这条链。

当前仍不包含：

- 更多真实榜单源、榜单增量监控与自动刷新
- 更多 metadata provider、provider 配置持久化与后台刷新
- 真实 PT 搜索命中质量优化、更多下载样例与 path handoff 稳定性收口
- 生产级订阅调度器能力、失败重试与真实整理规则
- 生产级下载完成回调、自动整理与媒体库刷新

手动初始化本地数据库：

```bash
cd backend
python -m app.db_init --reseed
```

当前执行模式说明：

- `metadata/*` 当前支持两种模式：
  - `seed`：本地 seed metadata
  - `musicbrainz`：实时查询 MusicBrainz Artist / Album / Track 搜索与详情；album detail 会从最佳 release 读取真实 track listing，track detail 的 related album 会对齐 release-group 语义。普通 keyword search 会按 MusicBrainz plain indexed search 语义带 `dismax=true`；recording detail 会直接请求 `release-groups`；album / track detail 还会补充最佳 release 的发行上下文，例如 `status`、`country`、`barcode`、`label_names`、`media_format`、`track_count`、`disc_count` 与 `secondary_types`；artist detail 还会补 discovery 更关心的上下文，例如 `sort_name`、`artist_type`、`area_name`、`begin_area_name`、`ended`、`release_group_count`、`primary_release_types`，以及 `featured_albums / featured_singles / featured_other_releases` 分类摘要
- `subscriptions/{id}/run` 为同步最小执行骨架，应用内 scheduler 会在 due 时触发同一条执行链；若最佳候选为 `AUTO_DOWNLOAD`，当前会继续自动 dispatch 并生成 organize preview；若 preview 已具备明确本地源文件，则继续自动 apply。对于 `path_handoff.handoff_status=pending_history_sync` 的已派发 run，scheduler 还会继续轮询宿主 download history：命中真实源文件后自动续跑 organize apply；超过 `host_handoff_pending_ttl_seconds` 仍未命中时，会把 organize record 标记为 `failed`，并在 run 摘要中写入 `handoff_unresolved`
- `charts/*` 当前支持三种模式：
  - `mock`：本地 chart seed
  - `listenbrainz`：真实 ListenBrainz sitewide artists / recordings；当前 detail 输出已补 discovery 产品化字段，如 chart summary、hero entry、entry groups，并统一产出 `MusicMediaInput`
  - `rss_feed`：按 settings 配置的 RSS feed 列表拉取，运行时优先读取项目 settings，环境变量仅作为 fallback；当前验证样本包括网易云热歌榜 playlist RSS、YouTube TopSongs RSS、YouTube TopArtists RSS，`item_count` 分别可写为 `200`、`100`、`100`。若项目 settings 和环境都未提供 `chart_rss_feeds`，fresh install 默认会带出 5 条内置 RSS feed：网易云热歌榜、网易云新歌榜、网易云原创榜、YouTube 热门歌曲榜、YouTube 热门歌手榜。RSS 条目现在统一映射为 `MusicMediaInput`，再构造成 `MusicMetaBase`，并通过 `recognition_state / recognition_note` 暴露是否足以继续识别；detail 下钻统一经由 `/media/resolve/detail` 驱动统一音乐媒体解析链。family-specific candidate hints 已下沉到 `MusicMetaBaseBuilder` / `MusicMediaRecognizer` 所消费的标准化输入里。对于 RSS chart entry 订阅，创建阶段会直接解析并持久化 `MusicMediaInput`、`MusicMetaBase` 与 `MusicMediaInfo` 相关快照，执行阶段若只有 input snapshot 也会通过统一链补全正式媒体对象
- `downloads/dispatch` 当前支持三类 host 语义：
  - 可靠 `media_in` -> `/api/v1/download/`
  - torrent-only 但已具备宿主媒体参考 -> `/api/v1/download/add`
  - 音乐 torrent-only 候选 -> 宿主 downloader runtime 直接提交下载器
- `organize/preview` 当前是 MusicPilot 本地音乐路径预览；`organize/apply` 当前通过宿主底层 file/storage 执行音乐文件整理。metadata 识别优先使用显式 detail，其次使用已有上下文、嵌入标签与 `source_path` 线索
- `jobs/*` 与 `downloads/dispatch` 会根据 host integration settings 在 mock 与 host 模式间切换
- 当前真实运行时不再根据验证矩阵决定业务路径；矩阵只保留为验证产物

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
export MUSICPILOT_HOST_SEARCH_MODE=prefer_host
export MUSICPILOT_HOST_DISPATCH_MODE=prefer_host
export MUSICPILOT_HOST_ORGANIZE_MODE=prefer_host
export MUSICPILOT_METADATA_PROVIDER_MODE=musicbrainz
export MUSICPILOT_METADATA_PROVIDER_TIMEOUT_SECONDS=15
export MUSICPILOT_METADATA_MUSICBRAINZ_BASE_URL=https://musicbrainz.org/ws/2
export MUSICPILOT_METADATA_PROVIDER_USER_AGENT='MusicPilot/0.1.0 (local)'
export MUSICPILOT_METADATA_CACHE_ENABLED=true
export MUSICPILOT_METADATA_CACHE_MAXSIZE=512
export MUSICPILOT_METADATA_SEARCH_CACHE_TTL_SECONDS=1800
export MUSICPILOT_METADATA_DETAIL_CACHE_TTL_SECONDS=21600
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
export MUSICPILOT_HOST_VALIDATION_MATRIX_PATH=/Users/me/path/to/MusicPilot/backend/data/host_validation_matrix.latest.json
```

启用 RSS chart provider 的最小配置示例：

```bash
export MUSICPILOT_CHART_PROVIDER_MODE=rss_feed
export MUSICPILOT_CHART_RSS_FEEDS='[
  {"id":"netease-liked","label":"网易云喜欢","url":"https://rsshub.app/163/music/playlist/9345476","category":"liked","region":"CN","enabled":true},
  {"id":"youtube-top-artists-us","label":"YouTube Top Artists US","url":"https://rsshub.app/youtube/charts/TopArtists/us","category":"top-artists","region":"US","enabled":true}
]'
```

当前运行态里，RSS feeds 也可以通过 `/settings/providers` 真实读写，保存后的配置会直接参与 charts discovery。

补充说明：

- `metadata` 与 `charts` 真实 provider 当前已支持最小 TTL 缓存
- 真正运行在宿主插件进程内时，优先复用 MoviePilot 推荐缓存接口
- backend 本地运行态与测试环境会自动回退到本地内存 TTL cache
- 第一阶段不包含复杂 RSS 可视化 CRUD
- 当前宿主会通过 `/api/v1/plugin/remotes` 加载 `static/remotes/<hash>/remoteEntry.js`，进入 MusicPilot 的远程 `Page`、`Dashboard` 与 `AppPage` 组件；本地独立前端开发页仍然保留用于日常开发。首页 dashboard 是否显示该卡片，仍受宿主 `Dashboard` 启用配置控制；宿主侧边栏入口则依赖 `/api/v1/plugin/sidebar_nav` 聚合已启用 Vue 插件的导航声明。

若没有真实宿主，可运行：

```bash
python3 ../scripts/host_integration_stub.py
```

然后通过 `/health`、`/api/probe/health`、`/api/probe/validation-matrix`、`/jobs/*`、`/downloads/dispatch` 与 `/organize/*` 查看当前 active adapter、backend、verification state、`path_handoff` 与验证产物。更完整的联调说明见 [docs/08_Phase5_宿主接入联调说明.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/08_Phase5_宿主接入联调说明.md)、[docs/09_Phase6_organize_联调说明.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/09_Phase6_organize_联调说明.md)、[docs/10_Phase7A_真实宿主语义验证与差异收敛.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/10_Phase7A_真实宿主语义验证与差异收敛.md)、[docs/11_Phase7B_真实成功样例闭环.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/11_Phase7B_真实成功样例闭环.md)、[docs/12_Phase8_真实成功率验证矩阵.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/12_Phase8_真实成功率验证矩阵.md)、[docs/14_架构收缩与语义归一说明.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/14_架构收缩与语义归一说明.md)、[docs/23_音乐文件整理技术设计与实现方案.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/23_%E9%9F%B3%E4%B9%90%E6%96%87%E4%BB%B6%E6%95%B4%E7%90%86%E6%8A%80%E6%9C%AF%E8%AE%BE%E8%AE%A1%E4%B8%8E%E5%AE%9E%E7%8E%B0%E6%96%B9%E6%A1%88.md) 和 [docs/28_项目整体任务盘点与执行路线.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/28_%E9%A1%B9%E7%9B%AE%E6%95%B4%E4%BD%93%E4%BB%BB%E5%8A%A1%E7%9B%98%E7%82%B9%E4%B8%8E%E6%89%A7%E8%A1%8C%E8%B7%AF%E7%BA%BF.md)。

当前固定调用规则与当前实现可这样理解：

- `history/download` 仍是新派发后的主 handoff 来源，`history/transfer` 只用于历史重放或补充查询
- `organize preview` 是 MusicPilot 本地音乐路径预览
- `organize apply` 是 MusicPilot 音乐路径规划 + 宿主底层 file/storage 执行
- 验证矩阵只保留为验证产物，不再描述当前 organize 主路径

Breaking cleanup 后，旧 SQLite 不再兼容当前 schema。请直接执行：

```bash
cd backend
python -m app.db_init --rebuild
```

手动回归真实宿主样例矩阵：

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot
backend/.venv/bin/python scripts/run_phase8_real_host_matrix.py --allow-side-effects
```

启动方式见仓库根目录 [README.md](../README.md)。
