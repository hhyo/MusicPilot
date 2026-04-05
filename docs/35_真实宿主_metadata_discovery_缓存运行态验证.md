# 35. 真实宿主 metadata / discovery 缓存运行态验证

## 目标

验证本轮新增的 metadata / discovery TTL 缓存，是否已经在 **真实 MoviePilot 插件进程** 中生效，而不只是本地单元测试通过。

本次验证只确认两点：

1. MusicBrainz metadata search / detail 的重复请求是否会命中缓存。
2. ListenBrainz charts list / detail 的重复请求是否会复用同一份缓存 payload。

## 验证环境

- MusicPilot 工作区：`/Users/lihuanhuan/PycharmProjects/MusicPilot`
- 宿主源码：`/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot`
- 宿主运行态：`CONFIG_DIR=/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/config-dev`
- 宿主 Python：`/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/.venv/bin/python`
- 插件安装目录：`/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/app/plugins/musicpilot`
- 插件数据库：`sqlite:////tmp/musicpilot-host-cache-validation.db`
- 鉴权：`X-API-KEY: moviepilot-dev-token`
- 元数据模式：`MUSICPILOT_METADATA_PROVIDER_MODE=musicbrainz`
- 榜单模式：`MUSICPILOT_CHART_PROVIDER_MODE=listenbrainz`
- scheduler：关闭

## 验证方法

为避免把“外网返回快慢”误当作缓存结论，本次验证使用 **宿主进程内的计数假客户端**：

1. 先将最新 `plugin_runtime/plugins/musicpilot` 同步到宿主 `app/plugins/musicpilot`。
2. 在宿主真实 Python 进程里：
   - `PluginManager().start("musicpilot")`
   - `register_plugin_api("musicpilot")`
3. 取出宿主插件运行时中的：
   - `app.plugins.musicpilot.core.dependencies.get_metadata_provider_adapter()`
   - `app.plugins.musicpilot.core.dependencies.get_chart_provider_adapter()`
4. 清空 adapter 自带缓存后，将 `_client` 替换成计数 fake client。
5. 通过宿主 `TestClient(app)` 重复调用插件 API：
   - `POST /api/v1/plugin/musicpilot/metadata/search`
   - `GET /api/v1/plugin/musicpilot/metadata/tracks/{id}`
   - `GET /api/v1/plugin/musicpilot/charts`
   - `GET /api/v1/plugin/musicpilot/charts/{chart_id}`
6. 统计 fake client 的真实命中次数。

说明：

- 这次验证的是“真实宿主插件进程中的缓存行为”。
- 不是在 MusicPilot 本地 backend 里直接 new adapter 做单测。

## 验证结果

宿主进程内脚本输出如下关键信息：

- `metadata_cache_uses_host_cache = true`
- `chart_cache_uses_host_cache = true`
- `metadata_search_statuses = [200, 200]`
- `track_detail_statuses = [200, 200]`
- `chart_statuses.list = 200`
- `chart_statuses.track_detail = 200`
- `chart_statuses.artist_detail = 200`

上游 fake client 实际命中次数：

- `metadata_search_call_count = 1`
- `metadata_detail_call_count = 1`
- `chart_recordings_call_count = 1`
- `chart_artists_call_count = 1`

对应请求序列为：

- metadata：
  - 第一次 `/metadata/search` 命中 `recording`
  - 第二次相同 `/metadata/search` 未再次命中上游
  - 第一次 `/metadata/tracks/cache-track-001` 命中 `recording/cache-track-001`
  - 第二次相同 detail 未再次命中上游
- charts：
  - `/charts` 首次拉取时命中：
    - `/1/stats/sitewide/artists`
    - `/1/stats/sitewide/recordings`
  - 随后的 `/charts/chart-listenbrainz-top-tracks-week`
  - 以及 `/charts/chart-listenbrainz-top-artists-week`
  - 都没有再次命中上游 payload

## 结论

可以确认：

1. MusicPilot 当前 metadata / discovery 缓存已经在真实宿主插件运行态中生效。
2. `RuntimeTTLCache` 在宿主插件进程内优先使用了宿主 `app.core.cache.TTLCache`，而不是本地 fallback cache。
3. 对于完全相同的 metadata search / detail 请求，以及 charts list / detail 请求：
   - API 仍返回 `200`
   - 上游 provider 实际只命中一次

这说明当前缓存实现不是“仅本地单测可用”，而是已经满足真实宿主插件运行态的最小可用要求。

## 当前边界

本次验证不包含：

- 外网真实 MusicBrainz / ListenBrainz 的响应时间对比
- cache hit/miss 指标对外暴露
- 跨进程、多实例共享缓存一致性验证

当前结论仅覆盖：

- 单宿主插件进程内
- 相同请求重复访问
- metadata / discovery provider payload 的 TTL 缓存行为
