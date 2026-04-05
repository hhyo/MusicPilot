# MusicBrainz Detail Enrichment Design

## Goal

在不改变现有插件 API 路径和主数据流的前提下，增强 MusicBrainz metadata detail 的结构化能力，让 `album detail` 与 `track detail` 更贴近真实音乐语义，并修正当前 detail 里的关联关系偏差。

## Current Problem

当前 `MusicBrainzMetadataProviderAdapter` 已经支持 Artist / Album / Track 搜索与详情，但 detail 仍有两处明显语义偏差：

1. `album detail` 里的 `tracks` 当前直接来自 `release-group.releases`，本质上是 release 列表，不是真实曲目列表。
2. `track detail` 里的 `related_album.id` 当前直接取 `recording.releases[0].id`，这是 release id，不稳定等价于 MusicPilot 当前 `/metadata/albums/{id}` 所使用的 release-group id。

这会导致：

- metadata 详情本身不够准确
- 前端详情抽屉里的 album track list 信息价值不足
- 后续 query builder / discovery / organize 如要继续复用 detail，会踩到错误关联语义

## Scope

本轮只增强 `MusicBrainz detail`，不扩到：

- 新 provider
- provider 聚合
- settings 持久化
- charts / subscription / dispatch / organize 主链
- 新 API 路径

## Design

### 1. Album detail 使用“两跳查询”

保留当前 `release-group/{id}` 作为专辑 detail 主入口，因为：

- 现有 `/metadata/albums/{album_id}` 路由已经把 `album_id` 定义成 release-group 语义
- QueryBuilder 和当前前端都已经围绕这个 id 工作

但在拿到 release-group detail 后：

- 选择一个“最佳 release”
- 再调用 `release/{release_id}?inc=recordings+artist-credits`
- 从 `media[].tracks[]` 中构造真正的 `tracks`

“最佳 release” 的最小选择规则：

1. 优先 `status=Official`
2. 再优先有最早 `date`
3. 最后回退到列表第一项

### 2. Track detail 修正 `related_album`

保留 `recording/{id}` 作为歌曲 detail 主入口，但 `related_album` 改为：

- `id` 使用 recording 对应 release 的 `release-group.id`
- `title` 使用 release title 或 release-group title
- 如果 recording 响应本身拿不到 `release-group`，则额外查询一次对应 `release/{id}`

这样前端从 track detail 点到 album detail 时，能稳定落到现有 `/metadata/albums/{release_group_id}`。

### 3. 补最小可复用字段

在保持现有 API 兼容的前提下，补一组对后续有价值但不扩散的可选字段：

- `MetadataReference.track_number`
- `MetadataReference.disc_number`
- `MetadataDetail.disambiguation`
- `MetadataDetail.release_count`

这些字段都是可选字段，不会破坏现有前端和 API 消费方。

## File Changes

- Modify: `backend/app/schemas/metadata.py`
- Modify: `backend/app/adapters/metadata_provider.py`
- Modify: `backend/tests/test_metadata_provider.py`
- Modify: `frontend/src/types/metadata.ts`
- Modify: `README.md`
- Modify: `backend/README.md`

## Testing

使用 TDD 覆盖三类行为：

1. `album detail` 返回真实 tracks，而不是 release 列表
2. `track detail.related_album.id` 对齐 release-group 语义
3. 新增可选字段存在时不破坏既有 API 结构

## Success Criteria

满足以下条件即视为完成：

- `MusicBrainzMetadataProviderAdapter.get_album_detail()` 返回的 `tracks` 来自 release track listing
- `MusicBrainzMetadataProviderAdapter.get_track_detail()` 返回的 `related_album.id` 可直接用于现有 album detail 路由
- 后端测试通过，前端类型同步，README/backend README 与当前 metadata 能力描述一致
