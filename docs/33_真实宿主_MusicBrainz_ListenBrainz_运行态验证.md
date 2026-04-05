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

## 验证 4：track chart entry -> subscription -> run

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

## 总结

当前真实宿主插件运行态下，已经成立的事实是：

1. `MusicBrainz metadata` 可用
2. `ListenBrainz charts` 可用
3. `track chart entry -> subscription -> run` 已能接到当前主链
4. 当前真正尚未完成的，不是 provider 接入，而是：
   - search/dispatch 的真实宿主/真实下载闭环
   - 拥有真实本地源文件后的自动 `apply`

## 下一步指向

从这次验证往下看，最值钱的下一步已经很明确：

- 不是继续补 provider
- 而是推进 **真实 acquisition / dispatch 主链**

也就是把当前：

`真实 metadata / 真实 charts -> mock search/dispatch -> preview`

继续推进成：

`真实 metadata / 真实 charts -> 真实 search/dispatch -> preview/apply`
