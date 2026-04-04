# Music Organize Metadata Resolver Extraction Design

## Goal

把当前 `OrganizeStrategyService` 里混合的“音乐元数据恢复”逻辑拆出来，形成一个独立的 `MusicMetadataResolver`，同时保持现有音乐 `preview/apply` 的外部语义、模板渲染规则和宿主执行路径不变。

这次设计只覆盖：

- 从 `candidate + metadata_detail` 恢复音乐整理上下文
- 让 `OrganizeStrategyService` 变成更薄的路径规划壳层

这次设计不覆盖：

- 模板规则重写
- `preview/apply` API 结构变更
- `path handoff / history / search / download` 调整
- 宿主执行层改造

## Context

当前真实链路已经证明：

1. `preview` 已经本地化为 MusicPilot 本地音乐路径预览。
2. `apply` 已经切到音乐路径规划 + 宿主底层文件执行。
3. 现在 `OrganizeStrategyService` 仍然同时做两件事：
   - 从 `MetadataDetail` 和 `SearchCandidateDetail` 恢复音乐命名上下文
   - 使用模板渲染相对路径和最终目标路径

这让 `OrganizeStrategyService` 仍然承担了两层职责，也让后续继续增强音乐元数据来源时必须直接改路径规划服务。

## Approaches Considered

### Option A: 保持现状，只在 `OrganizeStrategyService` 里继续加逻辑

优点：

- 代码改动最少

缺点：

- 元数据恢复和路径规划继续耦合
- 未来再补标签解析、文件名解析时会继续膨胀同一个文件
- `preview/apply` 共用逻辑的可测试边界不清楚

结论：不采用。

### Option B: 先拆 `MusicMetadataResolver`，保留现有模板渲染

优点：

- 改动最小但收益最大
- `preview` 和 `apply` 可直接复用统一元数据恢复逻辑
- 先把业务语义更重的一层抽出来，后面再拆 planner 会更顺

缺点：

- `OrganizeStrategyService` 仍然保留模板渲染和相对路径选择

结论：采用。

### Option C: 一次把 resolver + planner 都拆掉

优点：

- 结构最干净

缺点：

- 范围明显扩大
- 容易把当前“非破坏性收口”演变成重构
- 当前收益不值得一次做这么大

结论：本轮不采用。

## Chosen Design

### 1. New unit: `MusicMetadataResolver`

新增一个很薄的服务文件，例如：

- `backend/app/services/music_metadata.py`

职责只有一个：

- 根据 `SearchCandidateDetail + MetadataDetail | None` 恢复音乐整理上下文

它返回一个明确的值对象，而不是松散的 `dict`。推荐最小结构：

```python
MusicOrganizeMetadata(
    title: str,
    artist_name: str,
    album_title: str,
    track_title: str,
    year: str,
    format_ext: str,
)
```

其中字段语义保持和当前模板占位符一致，不引入新的模板变量。

### 2. Source precedence

`MusicMetadataResolver` 的字段恢复顺序保持当前行为，只把逻辑集中起来：

1. 优先使用 `metadata_detail` 中明确存在的音乐字段
2. 对 `artist / album / track` 分别根据 `entity_type` 做当前已有的回退
3. 最后使用 `candidate` 中已有的标题或站点字段做兜底
4. 所有字符串继续走现有 `slugify(...)`
5. `format_ext` 继续来源于 `candidate.format_tag`

这一点很重要：本轮不是“增强元数据恢复”，只是“把现有恢复逻辑从路径规划里抽出来”。

### 3. `OrganizeStrategyService` becomes a thin planner shell

`OrganizeStrategyService.build_plan(...)` 继续保留：

- `OrganizeStrategySnapshot` 构造
- `entity_type` 到 artist/album/track 相对路径的选择
- 模板渲染
- 最终 `target_library_path` 计算

但它不再直接自己组装上下文字段，而是：

1. 调用 `MusicMetadataResolver.resolve(...)`
2. 把返回值转成模板上下文
3. 使用现有 `_resolve_relative_path(...)` 和 `_render_template(...)`

### 4. API and runtime boundaries stay unchanged

这次拆分不改：

- `OrganizeService.preview()`
- `OrganizeService.apply()`
- `RealOrganizeAdapter.preview()/apply()`
- 插件前端调用
- organize record 结构
- host runtime bridge

也就是说，这次只是服务内聚度提升，不改变外部行为。

## Testing

最小测试应覆盖两类行为：

1. 新 resolver 自己的字段恢复优先级
   - `track` 实体
   - `album` 实体
   - `artist` 实体
   - 缺少 metadata 时的 candidate 回退

2. `OrganizeStrategyService.build_plan(...)` 外部行为不变
   - 现有路径规划测试继续通过
   - `preview/apply` 集成测试继续通过

## Success Criteria

以下条件同时满足即算完成：

1. 音乐元数据恢复逻辑不再散落在 `OrganizeStrategyService._build_context(...)`
2. 新 resolver 可以被单独测试
3. `OrganizeStrategyService.build_plan(...)` 输出结果与现有行为一致
4. `preview/apply` 的 API 语义、组织记录、真实宿主闭环都不受影响

## Spec Self-Review

- 无占位符、无 TBD
- 范围只覆盖 metadata resolver 抽离
- 不引入新模板变量或新 API
- 与当前 preview/apply 本地音乐语义一致
