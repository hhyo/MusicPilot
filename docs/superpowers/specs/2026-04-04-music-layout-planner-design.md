# Music Layout Planner Extraction Design

## Goal

把当前 `OrganizeStrategyService` 中负责“相对路径选择 + 模板渲染”的部分拆成独立的 `MusicLayoutPlanner`，让 organize 主链进一步收口成：

1. `MusicMetadataResolver`
2. `MusicLayoutPlanner`
3. `OrganizeStrategyService` 作为薄壳 plan 组装器

这次设计只覆盖：

- 相对路径层级选择
- 模板渲染
- `target_relative_path` 计算

这次设计不覆盖：

- `OrganizeStrategySnapshot` 结构变化
- `preview/apply` API 变更
- 模板变量扩展
- 音乐元数据来源增强
- 宿主文件执行层改造

## Context

当前仓库已经完成了第一步抽离：

- `MusicMetadataResolver` 已从 `OrganizeStrategyService` 中拆出
- `OrganizeStrategyService` 目前仍保留：
  - `snapshot` 构造
  - `entity_type` 到 artist/album/track 路径层级的选择
  - 模板渲染
  - `target_library_path` / `target_relative_path` 组装

这意味着 `OrganizeStrategyService` 仍然同时承担：

- planner orchestration
- layout rendering

继续把 layout 部分拆出，可以让 organize 这条音乐主链变成两个清晰的业务单元：

- 元数据恢复
- 路径规划

## Approaches Considered

### Option A: 保持现状

优点：

- 代码改动最少

缺点：

- `OrganizeStrategyService` 继续同时承担 orchestration 和 rendering
- 后续模板增强或多布局支持仍然会堆回同一个文件

结论：不采用。

### Option B: 只拆“相对路径选择 + 模板渲染”

优点：

- 范围最小
- 边界清楚
- 不改变现有 `OrganizePlan` 语义
- 与刚拆出的 `MusicMetadataResolver` 正好形成上下游边界

缺点：

- `OrganizeStrategyService` 仍保留 snapshot 构造

结论：采用。

### Option C: 把整个 `build_plan()` 全搬到 planner

优点：

- 结构更扁平

缺点：

- 会让 `OrganizeStrategyService` 几乎失去存在意义
- 本轮收益不够，像重命名多于拆分

结论：本轮不采用。

## Chosen Design

### 1. New unit: `MusicLayoutPlanner`

新增一个很薄的服务文件，例如：

- `backend/app/services/music_layout.py`

职责只有两个：

1. 根据 `MetadataDetail.entity_type` 决定 artist/album/track 路径层级
2. 根据模板和上下文渲染 `target_relative_path`

最小接口保持简单：

```python
class MusicLayoutPlanner:
    def build_relative_path(
        self,
        *,
        snapshot: OrganizeStrategySnapshot,
        context: dict[str, str],
        metadata_detail: MetadataDetail | None,
    ) -> str:
        ...
```

### 2. Rendering semantics remain unchanged

本轮不引入新的模板变量，也不改默认布局。

保留当前行为：

- `artist` 实体 -> artist dir
- `album` 实体 -> album dir
- `track` / 其他 -> `album dir + track file`
- `metadata_detail is None` -> artist dir
- 模板中未替换字段保持现有字符串替换模式
- 多余 `/` 继续压缩为单 `/`

### 3. `OrganizeStrategyService` becomes a thinner shell

`OrganizeStrategyService.build_plan(...)` 继续负责：

- `OrganizeStrategySnapshot` 构造
- 调用 `MusicMetadataResolver.resolve(...)`
- 组织模板上下文
- 调用 `MusicLayoutPlanner.build_relative_path(...)`
- 拼接 `target_library_path`
- 返回 `OrganizePlan`

它不再自己持有 `_resolve_relative_path(...)` 或 `_render_template(...)`。

### 4. External boundaries stay unchanged

这次拆分不改：

- `OrganizeService.preview()`
- `OrganizeService.apply()`
- `RealOrganizeAdapter.preview()/apply()`
- organize record
- 插件 API 路径
- 前端结构
- runtime bridge

也就是说，这次是纯内聚度提升，不改变外部行为。

## Testing

最小测试应覆盖：

1. `MusicLayoutPlanner` 自己的层级选择行为
   - artist 实体
   - album 实体
   - track 实体
   - `metadata_detail is None`

2. `OrganizeStrategyService.build_plan(...)` 输出结果保持不变
   - 现有路径规划断言继续成立
   - 现有 preview/apply 集成测试继续通过

## Success Criteria

以下条件同时满足即算完成：

1. 路径层级选择和模板渲染不再留在 `OrganizeStrategyService`
2. `MusicLayoutPlanner` 可以独立测试
3. `OrganizeStrategyService.build_plan(...)` 对外结果不变
4. `preview/apply`、真实宿主闭环、前端构建都不受影响

## Spec Self-Review

- 无占位符、无 TBD
- 范围只覆盖 layout planner 抽离
- 不引入新的模板语义
- 与当前 metadata resolver 抽离结果一致
