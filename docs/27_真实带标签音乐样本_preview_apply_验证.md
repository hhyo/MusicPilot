# 27. 真实带标签音乐样本 preview/apply 验证

## 目标

验证 `MusicMetadataResolver` 第二轮增强后的嵌入标签解析，是否能在**真实 MoviePilot 插件运行态**里真正影响：

1. `POST /api/v1/plugin/musicpilot/organize/preview`
2. `POST /api/v1/plugin/musicpilot/organize/apply`

本次验证不再停留在单元测试层，而是直接走：

- 宿主 `PluginManager` 加载后的 `musicpilot` 插件
- 宿主进程内 `TestClient(app)` 生命周期
- 真实插件 SQLite
- 真实插件 API 路由

## 验证环境

- MusicPilot 工作区：`/Users/lihuanhuan/PycharmProjects/MusicPilot`
- 宿主源码：`/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot`
- 宿主插件目录：`/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/app/plugins/musicpilot`
- 宿主运行配置：`CONFIG_DIR=/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/config-dev`
- 本次鉴权使用：`config-dev/app.env` 中的 `API_TOKEN`

本次运行时附加环境变量：

- `MUSICPILOT_HOST_INTEGRATION_ENABLED=true`
- `MUSICPILOT_HOST_ORGANIZE_MODE=prefer_host`
- `MUSICPILOT_HOST_ASSUME_ORGANIZE_AVAILABLE=true`
- `MUSICPILOT_ORGANIZE_ROOT_PATH=/Users/lihuanhuan/PycharmProjects/MusicPilot/.tmp/real-tagged-preview-apply/library`
- `MUSICPILOT_ORGANIZE_TRANSFER_TYPE=copy`

## 验证样本

样本故意做成“文件名和目录都错误，但嵌入标签正确”：

- 源文件路径：
  - `Wrong Artist/2001 - Wrong Album/01 - Wrong Song.m4a`
- 嵌入标签：
  - `title=Hello`
  - `artist=Adele`
  - `album=25`
  - `date=2015`

同时，为了让 layout planner 走 **track** 路径而不是 artist 路径，搜索任务的 `metadata_snapshot` 使用了最小 track detail：

- `entity_type=track`
- `title=Hello`
- `artist_name=None`
- `album_title=None`
- `track_title=None`
- `year=None`
- `release_type=album`

也就是说：

- `entity_type` 和 `release_type` 仍由 MusicPilot 自己给出
- `artist/album/year` 则要依赖嵌入标签恢复

## 验证步骤

1. 在宿主 Python 进程内生成真实 `.m4a` 音频文件。
2. 写入上述嵌入标签。
3. 在插件 SQLite 中写入最小 `SearchJobModel + SearchCandidateModel`。
4. 通过真实插件 API 调用：
   - `POST /api/v1/plugin/musicpilot/organize/preview`
   - `POST /api/v1/plugin/musicpilot/organize/apply`

## 验证结果

### 1. 嵌入标签确实进入了真实 preview 主路径

结果：

- `preview.status = 200`
- `preview.code = ORGANIZE_PREVIEW_OK`
- `data.organize_status = preview_ready`
- `data.target_relative_path = adele/2015 - 25/hello.m4a`
- `data.integration_point = RealOrganizeAdapter.preview.local_music_plan_preview`

这说明：

- 当前真实插件 API 下，`preview` 已经不是宿主影视 `transfer/name`
- 它确实使用了 MusicPilot 本地音乐 metadata 恢复 + layout planner
- 错误目录 `Wrong Artist/2001 - Wrong Album/01 - Wrong Song.m4a`
  被嵌入标签纠正成了：
  - `adele/2015 - 25/hello.m4a`

### 2. 嵌入标签同样影响了真实 apply 主路径

结果：

- `apply.status = 200`
- `apply.code = ORGANIZE_APPLY_OK`
- `data.organize_status = applied`
- `data.target_relative_path = adele/2015 - 25/hello.m4a`
- `data.integration_point = RealOrganizeAdapter.apply.music_storage_runtime_transfer`

目标文件实际落盘：

- `TARGET_EXISTS = true`
- `TARGET_SIZE_MATCH = true`

这说明：

- `apply` 使用的也是同一份 metadata 恢复与路径规划结果
- 最终执行的宿主底层文件操作与 preview 计算出的音乐路径一致

## 关键结论

本次验证已经证明：

1. `MusicMetadataResolver` 的嵌入标签解析不只是单元测试可用，而是在真实宿主插件运行态里确实生效。
2. 错误文件名/错误目录名不会覆盖更高优先级的嵌入标签。
3. 当前真实音乐 organize 闭环已经形成一致语义：
   - `preview`：本地音乐路径预览
   - `apply`：同一路径规划 + 宿主底层文件执行

## 边界说明

本次验证证明的是：

- 带标签的真实音乐文件在当前实现下可以正确 preview/apply

本次验证没有证明：

- 没有嵌入标签时所有样本都能稳定恢复 metadata
- 多碟专辑、合集、TV 类字段等更复杂路径规则已经完善
- 当前 metadata 恢复已达到生产级“全覆盖”

## 当前项目判断

到这一阶段，MusicPilot 的 organize 主链已经不是“概念验证”状态，而是：

- 真实插件加载：通过
- 真实插件 API：通过
- 真实音乐 `preview -> apply`：通过
- 真实带标签音乐样本闭环：通过

后续更高价值工作应转向：

1. 没有嵌入标签时的 metadata 恢复能力增强
2. 多碟/合集等音乐 layout 规则增强
3. 从 organize 单点能力，继续推进到订阅与下载后的自动闭环
