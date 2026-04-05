# 33. 真实宿主 MusicBrainz / ListenBrainz 运行态验证

## 目标

验证 `MusicBrainz metadata` 与 `ListenBrainz charts` 在 **真实 MoviePilot 插件进程** 中是否可用，并确认它们已经能和 `subscription run` 主链衔接。

## 验证环境

- 宿主源码路径：`/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot`
- 宿主运行态：`CONFIG_DIR=/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/config-dev`
- 宿主 Python：`/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/.venv/bin/python`
- 插件数据库：临时 `sqlite:////tmp/musicpilot-host-provider-runtime.db`
- 鉴权：`X-API-KEY: moviepilot-dev-token`
- 元数据模式：`MUSICPILOT_METADATA_PROVIDER_MODE=musicbrainz`
- 榜单模式：`MUSICPILOT_CHART_PROVIDER_MODE=listenbrainz`
- scheduler：关闭

## 验证 1：MusicBrainz metadata

调用：

- `POST /api/v1/plugin/musicpilot/metadata/search`
  - payload: `{"keyword":"Adele Hello","type":"track","page":1,"page_size":3}`
- `GET /api/v1/plugin/musicpilot/metadata/tracks/{id}`

结果：

- `metadata_search_status = 200`
- `metadata_search_source_type = musicbrainz_ws2`
- `metadata_search_provider = musicbrainz`
- `track_detail_status = 200`
- `track_detail_provider = musicbrainz`

结论：

- `MusicBrainzMetadataProviderAdapter` 已在真实宿主插件运行态中生效
- metadata 搜索与详情不再依赖本地 seed

## 验证 2：ListenBrainz charts

调用：

- `GET /api/v1/plugin/musicpilot/charts/providers`
- `GET /api/v1/plugin/musicpilot/charts`
- `GET /api/v1/plugin/musicpilot/charts/{chart_id}`

结果：

- `chart_providers_status = 200`
- `chart_providers_mock = false`
- `chart_list_status = 200`
- `chart_list_mock = false`
- `chart_count = 2`

当前真实榜单为：

- `chart-listenbrainz-top-artists-week`
- `chart-listenbrainz-top-tracks-week`

结论：

- `ListenBrainzChartProviderAdapter` 已在真实宿主插件运行态中生效
- 当前 chart 列表与详情不再来自 mock

## 验证 3：artist chart entry -> subscription -> run

使用榜单：

- `chart-listenbrainz-top-artists-week`

结果：

- `chart_sub_status = 200`
- `chart_run_status = 200`
- `chart_run_execution_status = manual_pending`
- `chart_run_matched_candidates_count = 3`
- `chart_run_mock = false`

解释：

- upstream metadata / chart 已是真实数据
- 但 artist 榜单项进入当前最小 run 骨架后，仍停在 `manual_pending`
- 这与当前主链的实体类型差异有关，不代表 provider 失效

## 验证 4：track chart entry -> subscription -> run（旧运行态结论）

使用榜单：

- `chart-listenbrainz-top-tracks-week`

结果：

- `chart_sub_status = 200`
- `chart_run_status = 200`
- `execution_status = dispatched`
- `matched_candidates_count = 3`
- `organize_status = preview_ready`
- `metadata_target_source_type = musicbrainz_ws2`
- `metadata_target_provider = musicbrainz`
- `search_job_status = dispatched`

`summary_json` 同时出现：

- `dispatch_status = mock_submitted`
- `dispatch_backend = mock`
- `binding_id = ...`
- `last_dispatched_candidate_id = ...`

结论：

- 真实 `ListenBrainz track chart` 已能创建真实订阅
- 真实订阅已能依赖 `MusicBrainz` metadata 进入当前主链
- 在当前 mock search/dispatch 运行态下，这条链会稳定推进到：
  - `dispatched`
  - `preview_ready`

## 2026-04-05 补充验证：真实 host search / dispatch 主阻塞定位

在当前最新 plugin runtime 下，又补做了两组更细的运行态核对。

### 1. 基准样本：Adele Hello

验证方式：

- `MUSICPILOT_METADATA_PROVIDER_MODE=seed`
- 使用 `track-hello`
- 不显式注入 `MUSICPILOT_HOST_*`，依赖插件运行态自动从宿主 `app.core.config` 派生 host 默认值

结果：

- `active_search_adapter = real_host_search`
- `candidate_count = 2`
- `results_total = 2`
- 候选标题示例：
  - `Adele - Hello 2015 - FLAC 分轨`

结论：

- 真实宿主插件运行态下，`real_host_search` 已经能在默认配置下真正工作
- `plugin runtime host defaults` 自动派生是有效的，不再需要手动导出 `MUSICPILOT_HOST_*`

### 2. 真实 ListenBrainz track 榜单样本：BTS - SWIM

验证方式：

- `MUSICPILOT_METADATA_PROVIDER_MODE=musicbrainz`
- `MUSICPILOT_CHART_PROVIDER_MODE=listenbrainz`
- 使用 `chart-listenbrainz-top-tracks-week` 的首条 track item

结果：

- `entry_title = BTS - SWIM`
- `execution_status = no_result`
- `search_job_status = no_result`
- `active_search_adapter = real_host_search`
- `candidate_count = 0`
- `ordered_queries` 为：
  - `BTS SWIM 2026 FLAC`
  - `BTS SWIM FLAC`
  - `BTS SWIM ARIRANG FLAC`
  - `BTS SWIM`
  - `SWIM`

结论：

- 这不是 plugin runtime 接线问题
- 也不是 provider 没有生效
- 当前失败点已经收敛成：**这类真实 track 样本在当前宿主 PT 搜索环境下没有命中结果**

进一步核对：

- 直接对真实宿主 `GET /api/v1/search/title` 发送以下查询：
  - `BTS SWIM FLAC`
  - `BTS ARIRANG FLAC`
  - `ARIRANG FLAC`
  - `BTS ARIRANG`
- 结果全部为：
  - `success = false`
  - `message = 未搜索到任何资源`

这说明当前 `BTS - SWIM` 的问题不只是“track title 查询太窄”，连更宽的 `artist + album` 变体在当前站点环境下也没有命中。

### 3. 真实 host dispatch 能力探测

直接读取宿主真实 endpoint：

- `GET /api/v1/download/clients`

结果：

- `200`
- 返回 `[]`

结论：

- 当前真实宿主环境里没有可用下载器
- 这解释了为什么 `dispatch_capability = false`
- 所以就算 real search 已经有结果，自动下载闭环也还会被 host 环境配置挡住

## 总结

当前真实宿主插件运行态下，已经成立的事实是：

1. `MusicBrainz metadata` 可用
2. `ListenBrainz charts` 可用
3. `real_host_search` 在真实宿主插件运行态下已确认可工作，Adele 基准样本能返回真实候选
4. `ListenBrainz` 的某些真实 track 样本在当前宿主 PT 搜索环境下仍会 `no_result`
5. 当前 host 运行态里 `downloaders` 为空，因此真实 dispatch 仍被环境配置阻断
6. 当前真正尚未完成的，不是 provider 接入，而是：
   - 真实 PT 搜索命中质量
   - 宿主下载器配置完成后的真实 dispatch 闭环
   - 拥有真实本地源文件后的自动 `apply`

## 下一步指向

从这次验证往下看，最值钱的下一步已经很明确：

- 不是继续补 provider
- 而是推进 **真实 acquisition / dispatch 主链**

也就是把当前：

`真实 metadata / 真实 charts -> 真实 search -> 真实 dispatch -> preview/apply`

继续推进成：

`真实 metadata / 真实 charts -> 真实 search(已验证) + 已配置下载器的真实 dispatch -> preview/apply`
