# MusicBrainz Release Context Enrichment

## Goal

继续只围绕 MusicBrainz 增强 metadata detail，把 album / track detail 里最有价值的 release 级上下文补齐，让 detail 更接近真实音乐发行信息。

## Why

当前 detail 已经修正了 release-group / release / recording 的关联语义，但 release 本身的重要上下文字段还没有进入 API：

- `status`
- `country`
- `barcode`
- `label-info`
- `media format`
- `track_count`
- `disc_count`
- `secondary-types`

这些字段都来自 MusicBrainz 官方 release / release-group 语义，对音乐详情展示、后续 query quality 和下载判断都比继续扩更多 provider 更值钱。

## Scope

本轮只做：

- `MetadataDetail` 增加可选 release-level 字段
- `album detail` 使用最佳 release detail 填充这些字段
- `track detail` 复用最佳 release / release-group 上下文填充最小 release-level 字段
- 前端 detail drawer 显示这些新增字段

不做：

- 新 provider
- 新 API 路径
- 持久化 release 缓存
- 更大范围搜索逻辑改造

## Fields

- `status`
- `barcode`
- `label_names`
- `media_format`
- `track_count`
- `disc_count`
- `secondary_types`

## Success Criteria

- album detail 能返回最佳 release 的发行上下文
- track detail 至少能返回同一最佳 release / release-group 的关键发行上下文
- 前端 detail drawer 能显示这些字段
- 定向与全量测试通过
