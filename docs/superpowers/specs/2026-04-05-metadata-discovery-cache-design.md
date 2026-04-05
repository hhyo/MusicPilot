# Metadata / Discovery Cache Design

## Goal

在不改变当前 `metadata` 与 `charts/discovery` 外部 API 语义的前提下，为真实 provider 输出增加最小缓存层，优先降低重复的 MusicBrainz / ListenBrainz 网络请求，并优先复用 MoviePilot 插件推荐的统一缓存接口。

## Scope

本轮只覆盖：

- `metadata/search`
- `metadata detail`
- `charts list`
- `charts detail`
- `charts entry`

本轮明确不做：

- 后台刷新
- 缓存持久化管理界面
- 多 provider 聚合缓存
- search job / subscription execution 级缓存

## Current State

- `MusicBrainzMetadataProviderAdapter` 每次 search/detail 都直接请求 WS/2。
- `ListenBrainzChartProviderAdapter` 每次 list/detail/entry 都直接请求 sitewide stats。
- 当前没有对 provider 输出做缓存，重复访问会直接重复请求上游。
- MoviePilot 插件 README 推荐插件优先使用 `app.core.cache.cached` / `TTLCache` / `Cache` 统一缓存接口。

## Design

### 1. Add a tiny runtime cache wrapper

新增一个很薄的 `backend/app/core/runtime_cache.py`：

- 优先尝试导入宿主 `app.core.cache.TTLCache`
- 如果当前不在宿主插件运行态，则回退到本地 `cachetools.TTLCache`
- 对上层只暴露极小接口：
  - `get(key, default=None)`
  - `set(key, value)`
  - `clear()`

这样可以同时满足：

- 宿主插件运行态优先复用官方推荐缓存
- backend 本地开发 / 单元测试继续可跑

### 2. Cache at provider boundary

缓存落在 provider adapter，而不是 service 或 route：

- `MusicBrainzMetadataProviderAdapter`
  - search result cache
  - detail cache
- `ListenBrainzChartProviderAdapter`
  - endpoint payload cache

这样 service 层保持无感知，仍然只关心 provider 语义。

### 3. Key strategy

- metadata search key：
  - `entity_type + normalized keyword + page + page_size`
- metadata detail key：
  - `entity_type + entity_id`
- chart payload key：
  - `path + stats_range + count`

### 4. TTL strategy

第一阶段使用固定 TTL：

- metadata search: 30 min
- metadata detail: 6 h
- chart payload: 15 min

这些 TTL 通过 `Settings` 暴露配置，但不做更复杂分层。

## Why this boundary

这是最小且高收益的切入点：

- 不改 API
- 不改 repository
- 不引入新的后台任务
- 对真实运行态最直接减少外部请求
- 与 MoviePilot 推荐缓存接口对齐

## Success Criteria

1. 相同 `metadata/search` 请求重复执行时，只命中上游一次。
2. 相同 metadata detail 请求重复执行时，只命中上游一次。
3. `charts list -> charts detail -> charts entry` 在相同 chart payload 下不重复命中 ListenBrainz。
4. 本地 backend 测试环境无需宿主 `app.core.cache` 也能正常运行。
