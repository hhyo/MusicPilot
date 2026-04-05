# PT Query Builder Design

## Goal

在不修改 search adapter、评分器和 dispatch 主链的前提下，优化 `QueryBuilderService` 产出的 `ordered_queries`，让真实音乐条目更符合 PT 站点常见的 release title 命名习惯，提高 `real_host_search` 的候选命中率。

## Problem

当前 `host_search` 只消费前 4 条正向查询词。现有 `QueryBuilderService` 的问题是：

- `track` 查询把 `year` 放得过前，容易把真实样本变窄。
- `track` 查询没有把 `artist + album + format` 这种更接近 PT 专辑包标题的组合提前。
- alias 查询优先级高于 relaxed 查询，容易把更值钱的 PT 风格基准查询挤出前 4 条。

这会导致真实 discovery / metadata 条目虽然是正确的，但在 PT 站点环境里仍然搜不到结果。

## PT 友好约束

这轮只做站点通用、风险较低的优化：

- 优先用 `artist + title/album + format`
- 对 `track` 条目优先覆盖“单曲标题”和“所在专辑包标题”两种常见 PT release 形态
- 让 `year` 从前置硬约束降级为次级查询
- alias 继续保留，但不再挤占前 4 条核心查询位

这轮不做：

- 站点专属模板
- 复杂多语言 transliteration
- feat./version 清洗规则扩展
- search adapter 行为变更

## Approaches

### A. 只增加更多查询词，不改顺序

优点：

- 实现最小

问题：

- `host_search` 只吃前 4 条，新增但排序不变几乎没有意义

结论：

- 不推荐

### B. 重排 track/album 查询优先级，并补最少量 PT 风格变体

做法：

- `track`：把 `artist + title + format`、`artist + album + format`、`artist + title + album + format` 提到前面
- `album`：保持 `artist + album + format` 为首选
- alias 查询整体后移到 relaxed 查询之后
- `year` 查询降级到 track/artist 的后段

优点：

- 不改 adapter
- 直接作用于前 4 条真实消费序列
- 风险和范围都很小

结论：

- 推荐

### C. 在 query builder 里引入站点模板或复杂规则

优点：

- 命中率上限更高

问题：

- 需要站点知识和更多运行态验证
- 容易把通用 query builder 变成站点耦合层

结论：

- 当前不做

## Recommended Design

采用 **方案 B**。

### Track query sequence

`track` 的核心正向查询顺序调整为：

1. `artist + track_title + format`
2. `artist + album_title + format`（如果有 album）
3. `artist + track_title + album_title + format`（如果有 album）
4. `artist + track_title`
5. `artist + album_title`
6. `artist + track_title + year + format`
7. `track_title`
8. aliases...

这样前 4 条会更像 PT 站点常见的：

- 单曲标题包
- 专辑整包
- 带专辑上下文的标题包
- 不带格式的宽松标题包

### Album query sequence

`album` 的核心正向查询顺序调整为：

1. `artist + album_title + format`
2. `artist + album_title + year + format`
3. `artist + album_title`
4. `album_title + format`
5. `album_title`
6. aliases...

### Artist query sequence

`artist` 先保持保守调整：

1. `artist`
2. `artist + year`
3. aliases...

Artist 主链当前不是 acquisition 主阻塞，所以这轮不深挖。

## Files

- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/services/query_builder.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_query_builder.py`
- Optional docs sync after verification:
  - `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/33_真实宿主_MusicBrainz_ListenBrainz_运行态验证.md`
  - `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/28_项目整体任务盘点与执行路线.md`

## Success Criteria

1. `track` 与 `album` 的前 4 条 `ordered_queries` 更符合 PT release title 习惯。
2. alias 查询不再挤占核心查询位。
3. 不修改 `host_search` adapter 逻辑，现有正向查询消费方式保持不变。
4. 全量测试继续通过。
