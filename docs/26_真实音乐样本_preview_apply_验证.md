# 26. 真实音乐样本 preview/apply 验证

## 目标

在已经完成“真实插件加载 + 宿主插件进程内执行 + 最小 `organize/apply` 闭环”验证之后，再用一条**真实音乐语义样本**验证：

1. `POST /api/v1/plugin/musicpilot/organize/preview`
2. `POST /api/v1/plugin/musicpilot/organize/apply`

在当前实现下分别会落到什么结果。

## 验证环境

- MusicPilot 工作区：`/Users/lihuanhuan/PycharmProjects/MusicPilot`
- 宿主源码：`/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot`
- 宿主运行配置：`CONFIG_DIR=/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/config-dev`
- 宿主插件：本地 `app/plugins/musicpilot`

本次运行时附加环境变量：

- `MUSICPILOT_HOST_INTEGRATION_ENABLED=true`
- `MUSICPILOT_HOST_ORGANIZE_MODE=prefer_host`
- `MUSICPILOT_HOST_ASSUME_ORGANIZE_AVAILABLE=true`
- `MUSICPILOT_HOST_BASE_URL=http://127.0.0.1:3001`
- `MUSICPILOT_HOST_AUTH_TOKEN=<host api token>`
- `MUSICPILOT_ORGANIZE_ROOT_PATH=/Users/lihuanhuan/PycharmProjects/MusicPilot/.tmp/real-music-preview-apply/library`
- `MUSICPILOT_ORGANIZE_TRANSFER_TYPE=copy`

## 验证样本

最小样本为：

- 本地单文件：`Adele - Hello.flac`
- `metadata_snapshot`：
  - `entity_type=track`
  - `artist_name=Adele`
  - `album_title=25`
  - `track_title=Hello`
  - `year=2015`
  - `format_tag=flac`

这意味着：

- MusicPilot 的本地音乐路径规划上下文是完整的
- `apply` 不需要再依赖影视 `MediaInfo / MediaType`
- `preview` 已本地化为 MusicPilot 的本地音乐 plan preview

## 验证结果

### 1. 真实音乐样本 `preview` 当前可用

调用：

- `POST /api/v1/plugin/musicpilot/organize/preview`

结果：

- `status=200`
- `code=ORGANIZE_PREVIEW_OK`
- `data.organize_status=preview_ready`
- `data.organizeable=true`
- `data.integration_point=RealOrganizeAdapter.preview.music_local_plan_preview`

这说明：

- 当前 `preview` 已经收口为本地音乐 plan preview
- 预览结果直接由 MusicPilot 的音乐 metadata snapshot 和本地路径规划生成
- 这条语义是给音乐整理做路径预览，不再借用宿主影视 transfer 语义

### 2. 同一样本 `apply` 当前成功

调用：

- `POST /api/v1/plugin/musicpilot/organize/apply`

结果：

- `status=200`
- `code=ORGANIZE_APPLY_OK`
- `data.organize_status=applied`
- `data.organize_backend=host`
- `data.integration_point=RealOrganizeAdapter.apply.music_storage_runtime_transfer`
- 目标文件实际复制到：
  - `/Users/lihuanhuan/PycharmProjects/MusicPilot/.tmp/real-music-preview-apply/library/adele/2015 - 25/hello.flac`

这说明：

- 当前音乐 `apply` 主路径已经和影视 `manual_transfer(...)` 脱钩
- MusicPilot 自己的音乐路径规划 + 宿主底层文件执行，这条路对真实音乐样本是成立的

## 结论

当前真实音乐样本下：

1. `preview` 和 `apply` 已经分别落在音乐预览语义与音乐执行语义上。
2. `preview` 现在是本地音乐 plan preview，因此返回 `preview_ready`。
3. `apply` 仍然是 MusicPilot 音乐语义 + 宿主底层文件执行，因此可以成功并返回 `applied`。

也就是说，当前系统状态不是：

- “preview/apply 都已完成音乐语义闭环”

而是：

- “preview 已完成本地音乐 plan preview”
- “apply 已完成音乐语义执行闭环”

## 下一步建议

如果继续推进，最合理的下一个问题不是再补 `apply`，而是明确选择其一：

1. 接受当前状态：
   - `preview` 作为本地音乐 plan preview 保留
   - 音乐 organize 的核心交付由 `preview_ready + applied` 这条链路共同完成
2. 单独重做音乐 `preview`：
   - 继续沿用 MusicPilot 本地音乐路径规划预览

在不改变现有结论的前提下，本次验证已经足够证明：

- 真实音乐样本上，当前真正可靠的是 `apply`
- 当前真正可读的预览语义已经本地化到 `preview`
