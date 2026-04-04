# Music Metadata Resolver Enhancement Design

## Goal

增强 `MusicMetadataResolver`，让 MusicPilot 在不引入新依赖、不改变 API、不改执行落点的前提下，更可靠地从现有上下文和 `source_path` 恢复音乐整理元数据。

这次设计同时收口当前仓库中已经过时的 organize 描述，让 README 和 backend README 回到当前真实实现状态。

## Scope

本次只覆盖：

- `MusicMetadataResolver` 第一轮增强
- 现有 `source_path` 的文件名/目录名解析
- README / backend README / 当前架构文档中的 organize 状态收口

本次不覆盖：

- 音频标签解析依赖接入
- 在线 metadata provider
- 新的前端输入
- `preview/apply` API 结构变化
- 宿主执行层调整

## Context

当前仓库已经完成：

- `preview` 本地音乐路径预览
- `apply` 音乐路径规划 + 宿主底层文件执行
- `MusicMetadataResolver` 与 `MusicLayoutPlanner` 的第一轮职责拆分

但 `MusicMetadataResolver` 目前仍然只吃：

1. `MetadataDetail`
2. `SearchCandidateDetail` 的少量基础字段

它还没有消化当前 organize 真实链路里已经掌握的另一类高价值输入：

- `candidate.raw_payload.host_transfer_source_path`
- `candidate.raw_payload.local_file_path`
- 基于源文件路径推导的文件名、父目录、祖父目录语义

这导致当前元数据恢复在缺少完整 `metadata_detail` 时过于依赖搜索阶段留下的字段，而没有充分利用已经拿到的本地音乐文件路径。

## Approaches Considered

### Option A: 直接引入音频标签解析

优点：

- 长期能力最强

缺点：

- 需要新依赖
- 测试样本和验证面会明显扩大
- 本轮目标会从“增强现有模型”变成“新能力接入”

结论：本轮不采用。

### Option B: 只增强已有上下文 + `source_path` 文件名/目录名解析

优点：

- 不引入新依赖
- 对真实音乐整理主链直接有收益
- 不改变现有外部边界
- 很适合作为音频标签解析前的第一轮增强

缺点：

- 不如标签解析稳定
- 对奇怪命名样本仍有限制

结论：采用。

### Option C: 同时做上下文增强和标签解析

优点：

- 一步到位

缺点：

- 范围过大
- 验证复杂度高
- 风险不符合当前“非破坏性推进”

结论：本轮不采用。

## Chosen Design

### 1. Keep current precedence, add path-derived hints

`MusicMetadataResolver` 的优先级保持“明确上下文优先”：

1. `MetadataDetail` 的明确字段
2. `candidate.raw_payload` 里已有的音乐字段
3. 从 `source_path` 派生的文件名/目录名线索
4. `candidate` 现有字段兜底

也就是说，本轮不是替换已有规则，而是给“没有完整 metadata_detail 的场景”增加更好的次级恢复来源。

### 2. Path-derived hint model

从 `source_path` 最小提取这些线索：

- `basename`：例如 `01 - Hello.flac`
- `stem`：例如 `01 - Hello`
- `parent_dir`：例如 `2015 - 25`
- `grandparent_dir`：例如 `Adele`

最小解析规则：

- `grandparent_dir` -> `artist_name` 候选
- `parent_dir` 若匹配 `YYYY - Album` -> `year` + `album_title`
- `parent_dir` 否则 -> `album_title` 候选
- `stem` 若匹配 `NN - Title` -> `track_title`
- `stem` 否则 -> `track_title` 候选

不在本轮做：

- 多碟目录 `Disc 1`
- 合辑识别
- feat./version 细分
- 轨道号单独建模

### 3. Existing public metadata model remains unchanged

`MusicOrganizeMetadata` 本轮不新增字段，仍然只返回：

- `title`
- `artist_name`
- `album_title`
- `track_title`
- `year`
- `format_ext`

这样可以保证：

- `MusicLayoutPlanner` 无需改接口
- `OrganizeStrategyService` 无需改 plan 结构
- `preview/apply` 无需改 API

### 4. Lightweight parser stays inside `music_metadata.py`

本轮不再额外新建一个“path parser 框架”。

为保持最小范围，解析辅助函数直接留在：

- `backend/app/services/music_metadata.py`

如果后续继续加标签解析，再考虑拆出更独立的 parser。

### 5. Doc state cleanup

当前 README 和 backend README 还残留一些已经过时的 organize 描述，例如：

- `preview` 仍映射 `/api/v1/transfer/name`
- `apply` 仍描述为 `transfer/manual` 或 `manual_transfer` 成功链

这次一并收口成当前真实状态：

- `preview` = MusicPilot 本地音乐路径预览
- `apply` = MusicPilot 音乐路径规划 + 宿主底层 file/storage 执行

历史文档仍保留，但当成历史记录，不当成当前行为说明。

## Testing

最小测试应覆盖：

1. `source_path` 可恢复 artist/album/title/year
2. `MetadataDetail` 仍覆盖 path hints
3. 无 `source_path` 时仍保持当前 fallback 行为
4. `OrganizeStrategyService.build_plan(...)` 因 resolver 增强而得到更稳定的相对路径
5. 现有 `preview/apply` 集成测试仍通过

## Success Criteria

以下条件同时满足即算完成：

1. `MusicMetadataResolver` 能利用 `source_path` 恢复更好的音乐上下文
2. 没有 `MetadataDetail` 时，整理路径不再只依赖 `candidate.title/site_name`
3. `preview/apply` API 和执行落点不变
4. README / backend README 中的 organize 现状描述与真实实现一致

## Spec Self-Review

- 无占位符、无 TBD
- 范围只覆盖 metadata resolver 第一轮增强和文档状态收口
- 不引入新依赖或新 API
- 与当前 preview/apply 的音乐语义一致
