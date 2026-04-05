# 30. ListenBrainz 榜单运行态验证

## 结论

MusicPilot 当前已经支持 `MUSICPILOT_CHART_PROVIDER_MODE=listenbrainz`，并在本地运行态下完成了真实榜单 provider 的 smoke check。

当前已验证通过：

- `GET /api/v1/plugin/musicpilot/charts/providers`
- `GET /api/v1/plugin/musicpilot/charts`
- `GET /api/v1/plugin/musicpilot/charts/{chart_id}`
- `POST /api/v1/plugin/musicpilot/charts/{chart_id}/subscribe`
- `POST /api/v1/plugin/musicpilot/subscriptions/{id}/run`

当前返回语义：

- `mock=false`
- `provider=listenbrainz`
- `source_type=listenbrainz_sitewide_stats`

## 验证方式

- 使用 `TestClient`
- 设置：
  - `MUSICPILOT_CHART_PROVIDER_MODE=listenbrainz`
  - `MUSICPILOT_CHART_PROVIDER_USER_AGENT=MusicPilot/0.1.0 (chart-runtime-smoke)`
  - `MUSICPILOT_CHART_LISTENBRAINZ_RANGE=week`
- 请求：
  - `GET /api/v1/plugin/musicpilot/charts/providers`
  - `GET /api/v1/plugin/musicpilot/charts`
  - `GET /api/v1/plugin/musicpilot/charts/chart-listenbrainz-top-artists-week`
  - `POST /api/v1/plugin/musicpilot/charts/chart-listenbrainz-top-artists-week/subscribe`
  - `POST /api/v1/plugin/musicpilot/subscriptions/{id}/run`

## 结果

- provider 列表返回 `200`
- 返回体 `mock=false`
- provider `chart_source=listenbrainz`
- charts 列表返回 `200`
- 当前返回两张真实榜单：
  - `chart-listenbrainz-top-artists-week`
  - `chart-listenbrainz-top-tracks-week`
- chart detail 返回 `200`
- artist chart entry 的 `target_id` 为 `artist_mbid`
- track chart entry 的 `target_id` 为 `recording_mbid`
- chart entry 订阅创建返回 `200`
- 使用 artist chart entry 创建的订阅可以成功进入手动 `run`
- 当时的 `run` 已能走到：
  - `metadata detail`
  - `search job`
  - `organize preview`
- 当时的 execution status 仍停在现阶段获取链的 `manual_pending`，这不是 chart provider 阻塞。当前主链已继续推进到自动 dispatch，并会在具备明确本地源文件时继续自动 apply。

## 当前边界

- 当前只接入 ListenBrainz `sitewide artists` 与 `sitewide recordings`
- 当前没有真实专辑榜
- 当前没有榜单快照持久化
- 当前没有榜单增量比对与自动刷新
- 当前没有多 provider 聚合
- 当前 chart subscription run 仍受后续 acquisition / dispatch 自动化能力约束

## 当前价值

第一版真实 discovery 已经不再是 mock-only：

- 榜单列表与详情来自真实 provider
- chart entry 的 `target_id` 已与当前 MusicBrainz metadata 主链对齐
- 真实 chart entry 已可进入当前订阅执行主链
- 这为后续真实 chart subscription run 自动化与 discovery 增量监控奠定了最小可用基础

## 当前产品化状态

当前 discovery 已经开始从“原始榜单 API 查看器”收口成产品化发现页：

- chart list 当前会带出 `summary`、`chart_group`、`chart_scope`、`freshness_label`
- chart detail 当前会带出 `hero_entry`、`entry_groups`、`conversion_summary`
- 每个 chart entry 当前都映射到稳定的 `DiscoveryTarget`
- 后续 `discovery -> metadata` 转化将以 `DiscoveryTarget` 为唯一桥接层，而不是继续依赖 provider 原始 payload
