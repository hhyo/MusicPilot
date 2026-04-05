# ListenBrainz Chart Provider Design

## Goal

为 MusicPilot 的 `charts` 模块接入第一条真实榜单源，替换当前纯 `local seed / mock chart source` 的发现入口，同时保持现有图表路由、订阅入口和前端页面结构不变。

## Why ListenBrainz

第一版不选 Apple Music / iTunes RSS，原因不是接口不可用，而是它返回的 song / release 标识与当前 `MusicBrainzMetadataProviderAdapter` 不对齐。榜单条目如果不能稳定映射到后续 `metadata detail -> search job -> subscription run` 链路，就只能把 discovery 变成新的孤岛。

ListenBrainz 的 `sitewide stats` 公开 API 有两个优势：

- 返回 `artist_mbid` 与 `recording_mbid`
- 这些 MBID 可直接作为当前 metadata 主链的 `EntityType.ARTIST` / `EntityType.TRACK` detail 输入

这使得榜单条目不仅能展示，还能被当前订阅链正确消费。

## Scope

本轮只接入：

- `sitewide artists`
- `sitewide recordings`

本轮不接：

- `sitewide releases`
- Apple / QQ / 网易云 / Bilibili 真实榜单
- 榜单增量监控
- 榜单刷新持久化
- 多 provider 聚合

`sitewide releases` 暂不接入，是因为当前 metadata 的专辑 detail 使用的是 MusicBrainz `release-group` 语义，而 ListenBrainz 返回的是 `release_mbid`。这会让 chart entry 的 `target_id` 和后续 metadata detail 链路不一致。

## Runtime Shape

### Provider mode

新增 `chart_provider_mode`：

- `mock`：保留当前本地 seed/mock
- `listenbrainz`：使用真实 ListenBrainz 榜单

### Provider outputs

在 `listenbrainz` 模式下：

- `/charts/providers` 返回一个真实 provider：`listenbrainz`
- `/charts` 返回两张榜单：
  - `chart-listenbrainz-top-artists-week`
  - `chart-listenbrainz-top-tracks-week`
- `/charts/{chart_id}` 返回对应榜单条目
- `/charts/{chart_id}/subscribe` 继续沿现有 chart entry 订阅结构创建订阅

### Entry mapping

#### Artist chart entry

- `item_type = artist`
- `target_id = artist_mbid`
- `target_name = artist_name`
- `subtitle = "{listen_count} listens"`

#### Track chart entry

- `item_type = track`
- `target_id = recording_mbid`
- `target_name = track_name`
- `subtitle = artist_name`

这保证了：

- artist 订阅后可直接查 MusicBrainz artist detail
- track 订阅后可直接查 MusicBrainz recording detail

## Integration boundary

保留现有边界不变：

- `ChartProviderAdapter`
- `ChartService`
- `/api/v1/plugin/musicpilot/charts/*`
- 前端 `ChartsView`

只做最小增强：

- 在 `ChartProviderAdapter` 上补 provider/source/mock 语义
- 增加 `ListenBrainzChartProviderAdapter`
- 让 `ChartService` 和 chart routes 的 `mock / note / integration_point` 根据 adapter 动态输出

## Config

新增配置：

- `MUSICPILOT_CHART_PROVIDER_MODE`
- `MUSICPILOT_CHART_LISTENBRAINZ_BASE_URL`
- `MUSICPILOT_CHART_PROVIDER_TIMEOUT_SECONDS`
- `MUSICPILOT_CHART_PROVIDER_USER_AGENT`
- `MUSICPILOT_CHART_LISTENBRAINZ_RANGE`
- `MUSICPILOT_CHART_LISTENBRAINZ_COUNT`

默认值保持开发友好：

- mode 默认 `mock`
- range 默认 `week`
- count 默认 `20`

## Testing

需要三层验证：

1. adapter mapping 单测
2. `ChartService` 在 live mode 下的语义单测
3. runtime smoke check

runtime smoke check 只验证：

- `/charts/providers`
- `/charts`
- `/charts/{chart_id}`

不把这轮扩大到完整 chart subscription run 验收。

## Success criteria

- `listenbrainz` 模式下 `/charts` 不再返回 mock 语义
- 榜单条目 `target_id` 与当前 MusicBrainz metadata 主链对齐
- 前端榜单页在真实模式下可以正常展示 provider / chart / chart detail
- `mock` 模式仍保持现有行为
