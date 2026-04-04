# Music Metadata Tag Parsing Design

## Goal

增强 `MusicMetadataResolver`，在不改变 `preview/apply` API、不中断当前 organize 执行边界的前提下，优先从真实本地音频文件的嵌入标签恢复音乐整理元数据。

## Scope

本次只覆盖：

- `MusicMetadataResolver` 第二轮增强
- 在 `source_path` 指向真实音频文件时读取最小标签集
- 依赖与文档同步

本次不覆盖：

- 新的前端输入
- 在线 metadata provider
- `preview/apply` 执行逻辑调整
- 宿主 file/storage 执行层调整
- 多文件专辑级标签聚合

## Context

当前仓库已经完成：

- `preview` = MusicPilot 本地音乐路径预览
- `apply` = MusicPilot 音乐路径规划 + 宿主底层 file/storage 执行
- `MusicMetadataResolver` 第一轮增强：可从 `MetadataDetail`、`candidate.raw_payload`、`source_path` 文件名/目录名恢复 artist/album/title/year/format

但当前 resolver 仍有明显缺口：

- 当 `MetadataDetail` 缺失或不完整时，只能依赖文件名和目录名猜测
- 对命名不规整但标签完整的音频文件支持不足

## Chosen Design

### 1. Add embedded-tag hints as a new mid-priority source

`MusicMetadataResolver` 的优先级调整为：

1. `MetadataDetail`
2. `candidate.raw_payload` 的明确音乐字段
3. 真实本地音频文件的嵌入标签
4. `source_path` 派生的文件名/目录名 hints
5. `candidate` 现有字段兜底

这意味着：

- 显式 metadata 仍然最高优先级
- 标签只作为路径猜测之上的可靠补充
- 没有真实文件或标签读取失败时，当前行为保持不变

### 2. Use `mutagen` as the minimal tag reader

选择 `mutagen`，原因：

- Python 生态里稳定、常用
- 只读标签能力足够覆盖当前需求
- 支持 `FLAC`、`MP3/ID3`、`M4A/MP4` 等常见音频格式

本轮只读取最小字段：

- `title`
- `artist`
- `album`
- `date/year`
- `tracknumber`

不在本轮做：

- 专辑艺术家优先级扩展
- 碟号、合辑、作品/演奏者复杂标签
- 封面、歌词、BPM 等额外音频元数据

### 3. Keep the public metadata model unchanged

`MusicOrganizeMetadata` 仍然只暴露：

- `title`
- `artist_name`
- `album_title`
- `track_title`
- `year`
- `format_ext`

标签解析结果只用于填充这些已有字段，不新增 public schema。

### 4. Keep the parser local to `music_metadata.py`

本轮不再额外创建完整 tag framework。

最小实现方式：

- 在 `music_metadata.py` 内新增私有标签读取辅助逻辑
- 对 `mutagen` 进行软导入
- 当文件不存在、格式不支持、读取失败时静默降级到现有路径 hints

### 5. Current-state docs should mention embedded-tag support

需要同步当前状态文档，避免 README 仍然只描述“路径 hints”：

- `README.md`
- `backend/README.md`
- `docs/23_音乐文件整理技术设计与实现方案.md`

历史文档不回写，不重写阶段记录。

## Data Mapping

最小标签映射规则：

- `title` <- `title`
- `artist_name` <- `artist`
- `album_title` <- `album`
- `track_title` <- `title`
- `year` <- `date` / `year` 的 4 位年份
- `format_ext` 仍优先 `candidate.format_tag`，否则取文件后缀

### Track number

本轮读取 `tracknumber`，但只作为未来能力预留：

- 不新增到 `MusicOrganizeMetadata`
- 不改变 layout planner 接口
- 仅在内部读取，为后续 `NN - Title` 命名增强留入口

## Failure Handling

以下场景都必须无破坏降级：

- `source_path` 不存在
- `source_path` 不是本地文件
- 文件格式不支持
- `mutagen` 读取异常
- 标签字段为空

这些情况下 resolver 继续走当前路径 hints/fallback 行为，不改变 API 语义。

## Testing

最小测试覆盖：

1. 当 `MetadataDetail` 缺失时，标签可覆盖路径 hints
2. 当 `MetadataDetail` 存在时，标签不会覆盖显式 metadata
3. 标签读取失败时，resolver 保持当前路径 hints 行为
4. `OrganizeStrategyService.build_plan(...)` 能从标签驱动出更稳定的目标路径

## Success Criteria

以下条件同时满足即算完成：

1. `MusicMetadataResolver` 能在本地真实音频文件存在时读取嵌入标签
2. 没有 `MetadataDetail` 时，标签优先级高于路径 hints
3. 没有标签或读取失败时，现有行为不退化
4. `preview/apply` API、执行边界、宿主 file/storage 路径不变

## Spec Self-Review

- 无占位符、无 TBD
- 范围只覆盖第二轮 metadata 增强
- 不改变外部 API 与 organize 运行边界
- 与当前 `MusicMetadataResolver -> MusicLayoutPlanner -> host storage runtime` 架构一致
