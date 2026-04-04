# Music Organize Preview Localization Design

## Goal

把 MusicPilot 的 `organize preview` 从宿主影视 `transfer/name` 语义中剥离出来，改成 **MusicPilot 本地音乐路径预览**。

本次设计只覆盖 `preview`：

- 不修改 `apply` 的宿主底层文件执行路径
- 不修改 `path handoff / history / search / download`
- 不修改插件前端 API 路径与请求结构

## Context

当前真实验证已经证明：

1. `apply` 已经可以在真实宿主插件 API 下对音乐样本成功执行。
2. `preview` 仍然映射到宿主 `/api/v1/transfer/name`。
3. 对真实音乐样本，`preview` 会返回 `未识别到媒体信息`，而 `apply` 却可以成功。

这意味着当前 `preview` 与 `apply` 已经不再共享同一业务语义：

- `preview` 仍是影视命名预览
- `apply` 已是音乐路径规划 + 宿主底层文件执行

## User-Facing Decision

`preview` 的职责定义为：

- **回答“如果现在整理，MusicPilot 计划把文件放到哪里”**
- **不负责保证此刻一定能执行成功**

也就是说，`preview` 是 **路径预览**，不是 **可执行预检**。

## Approaches Considered

### Option A: 继续复用宿主 `transfer/name`

优点：

- 现有代码改动最少

缺点：

- 仍然是影视语义
- 对真实音乐样本已被验证为错误
- 继续保留会让 `preview` 与 `apply` 永久分叉

结论：不采用。

### Option B: 本地音乐路径预览 + 宿主可执行性预检

优点：

- 预览更接近真正执行结果

缺点：

- 会把 `preview` 重新耦合到底层执行状态
- 容易把 `preview` 做成半个 `apply`
- 范围扩大，收益不成比例

结论：不采用。

### Option C: 纯本地音乐路径预览

优点：

- 语义与 MusicPilot 对齐
- 和当前已成功的 `apply` 路径一致
- 实现最小、边界最清楚

缺点：

- 不能提前暴露所有执行时错误

结论：采用。

## Chosen Design

### 1. Preview data source

`preview` 继续复用现有 `OrganizeService.preview()` 和 `OrganizeStrategyService.build_plan(...)`。

输入仍来自：

- `candidate`
- `metadata_detail`
- 现有 `source_path/source_filetype`

但不再调用宿主 `/api/v1/transfer/name`。

### 2. Preview result semantics

`RealOrganizeAdapter.preview()` 改成直接返回本地音乐预览结果：

- `organize_backend=host`
- `adapter_mode=host`
- `organize_status=preview_ready`
- `organizeable=True`
- `target_library_path=plan.target_library_path`
- `target_relative_path=plan.target_relative_path`

只要当前 candidate 有明确 organize input，就返回预览成功。

如果连最基本 organize input 都没有，例如：

- 缺少 `source_path`
- 缺少候选上下文

则维持当前直接失败语义。

### 3. Error boundary

`preview` 不再做以下检查：

- 宿主 `transfer/name` 媒体识别
- 目标目录是否当前可访问
- 底层 storage oper 是否当前可用
- transfer type 是否当前支持

这些继续由 `apply` 暴露。

### 4. Integration point naming

新的 preview integration point 应明确反映本地音乐语义，例如：

- `RealOrganizeAdapter.preview.music_local_plan_preview`

而不是继续出现 `moviepilot_transfer_name`。

## Architecture Impact

这次只改一个点：

- [organize.py](/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/organize.py)

服务层、路由层、前端 API 调用都保持不变。

## Testing

最小测试覆盖：

1. 真实 organize input 存在时，`RealOrganizeAdapter.preview()` 不再调用 host HTTP client
2. 真实 organize input 存在时，preview 返回 `preview_ready`
3. 缺少 `source_path` 时，仍然直接失败
4. 真实宿主插件 API 音乐样本下：
   - `preview` 变为 `preview_ready`
   - `apply` 保持 `applied`

## Non-Goals

本次不做：

- preview 的宿主执行预检
- 音频标签解析增强
- 新的音乐 metadata 模型拆分
- preview/apply 合并为同一执行器
- 对 `apply` 路径的任何结构变更

## Success Criteria

以下条件同时满足即算完成：

1. 对真实音乐样本，`POST /organize/preview` 不再因为影视识别失败而报错
2. `preview` 返回的目标路径与当前 `apply` 最终执行路径一致
3. `apply` 现有成功路径不被破坏
4. 插件前端 API 路径、请求结构、返回结构不变

## Spec Self-Review

- 无占位符、无 TBD
- 范围只覆盖 `preview` 本地化
- 与当前 `apply` 音乐执行路径不冲突
- 成功标准可直接用于下一步实现和验收
