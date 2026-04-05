# MusicBrainz Artist Discovery Summary

## Goal

作为 metadata 线最后一轮 artist detail 优化，把 MusicBrainz artist detail 从“完整 release-group 列表”进一步收口成更适合 discovery / 订阅入口直接消费的分类摘要。

## Why

当前 artist detail 已经带出：

- `release_group_count`
- `primary_release_types`
- 排序后的 `related_albums`

但 discovery 侧真正更关心的是：

- 这个艺人的代表性专辑有哪些
- 近期单曲有哪些
- 还有多少其他 release-groups 被折叠在后面

继续补更多底层字段的收益已经不高，下一步更值钱的是把 release-group 直接整理成可浏览摘要。

## Scope

本轮只做：

- `featured_albums`
- `featured_singles`
- `featured_other_releases`
- `featured_release_group_counts`

保持：

- 现有 `related_albums` 不删，继续保留兼容
- 不新增路由
- 不引入新 provider

## Design

- `featured_albums`：从 artist 的 release-groups 中筛出 `Album`，按当前排序规则取前 3
- `featured_singles`：筛出 `Single`，取前 3
- `featured_other_releases`：其余类型，取前 3
- `featured_release_group_counts`：返回 `album / single / other / total` 四个计数

subtitle 继续沿用当前 `PrimaryType · Year` 格式。

## Success Criteria

- artist detail API 能返回 discovery 友好的分类摘要
- 前端 detail drawer 能优先展示这三组 summary
- 现有 `related_albums` 兼容保留
