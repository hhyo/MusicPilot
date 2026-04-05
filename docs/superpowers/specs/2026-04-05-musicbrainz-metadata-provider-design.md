# MusicBrainz Metadata Provider Design

## Goal

接入一个最小可交付的真实 metadata provider，先覆盖 Artist / Album / Track 的搜索与详情，不改前端 API，不改 organize/discovery/scheduler。

## Boundary

- 继续保留本地 seed 作为默认模式和开发数据
- 新增 `musicbrainz` provider 模式
- `MetadataService` 在 live provider 模式下直接委托 adapter 做 search/detail
- 不修改 SearchJob / QueryBuilder / organize 的外部接口

## First implementation

1. 在 `metadata_provider.py` 中新增 `MusicBrainzMetadataProviderAdapter`
2. 扩展 `MetadataProviderAdapter` 支持 `supports_live_queries/search/get_detail`
3. `MetadataService` 在 live provider 模式下绕过本地 repository 搜索与详情查询
4. `dependencies.py` 根据配置选择 `MockMetadataProviderAdapter` 或 `MusicBrainzMetadataProviderAdapter`
5. 新增最小配置项：provider mode / base url / timeout / user agent

## Non-goals

- 不接 charts
- 不做 provider 聚合
- 不做缓存层
- 不做音频标签和在线 metadata 融合
