# 21. organize apply 输入模型增强

## 目标

本轮只做一件事：

- 在不改变 `TransferChain.manual_transfer(...)` 接入落点的前提下，增强 MusicPilot 传给宿主的 apply 输入模型。

本轮不做：

- preview 调整
- path handoff / history 职责调整
- 搜索 / 下载主链路语义调整
- 新的 strategy / matrix / fallback 抽象

## 本轮新增透传字段

当前 `RealOrganizeAdapter.apply()` 在原有参数基础上，新增透传以下字段：

| 字段 | 来源 | 用途 |
| --- | --- | --- |
| `tmdbid` | `candidate.raw_payload.host_media_reference.tmdbid`，其次 `candidate.raw_payload.host_context.media_info.tmdb_id` | 命中宿主显式媒体识别分支 |
| `doubanid` | `candidate.raw_payload.host_media_reference.doubanid`，其次 `candidate.raw_payload.host_context.media_info.douban_id` | 命中宿主显式媒体识别分支 |
| `download_hash` | `candidate.raw_payload.path_handoff.download_hash` | 命中宿主下载历史查询分支 |
| `downloader` | `binding.target_downloader`，在 `OrganizeService._resolve_context()` 中注入为 `candidate.raw_payload.host_transfer_downloader` | 与 `download_hash` 组合补全下载上下文 |

## 为什么先补这四个

原因很直接：

1. 这四个字段已经在现有 MusicPilot 数据链路里存在或可恢复。
2. 它们与宿主 `manual_transfer(...)` 的实际参数语义一一对应。
3. 它们能最大程度减少宿主对纯文件名/目录名识别的依赖。
4. 补这四个字段不需要改变插件 API 输入，也不需要重划 `path handoff` 或 `history` 的职责。

## 本轮暂不补的字段

| 字段 | 当前不补原因 |
| --- | --- |
| `mtype` | 当前 MusicPilot 没有稳定、可信的影视类型来源；硬补容易伪造 |
| `season` | TV 语义字段，当前音乐主链路没有稳定来源 |
| `episode_group` | 同上 |
| `epformat` | 需要 TV 自定义集数格式输入，当前链路没有可靠来源 |

## 当前边界保持不变

以下边界在本轮保持不变：

- `POST /api/v1/plugin/musicpilot/organize/apply` 请求结构不变
- `RealOrganizeAdapter.apply()` 的宿主接入落点不变，仍为 `TransferChain.manual_transfer(...)`
- preview 不变
- path handoff / history 职责不变
- organize record 写回语义不变
- 失败语义不变：没有增强字段时，继续按当前失败路径直出

## 代码改动范围

本轮实际只增强了三层最小映射：

1. `OrganizeService._resolve_context()`
   - 从 binding 上下文补 `path_handoff`
   - 从 binding 上下文补 `host_transfer_downloader`
2. `RealOrganizeAdapter._build_manual_transfer_args()`
   - 从 candidate/raw payload 中抽取新增字段
3. `HostTransferRuntimeBridge.manual_transfer()`
   - 把新增字段继续透传到宿主 `TransferChain.manual_transfer(...)`

## 当前结论

这轮输入模型增强完成后，MusicPilot 对宿主 apply 的输入已经从：

- `fileitem`
- `target_path`
- `transfer_type`

增强为：

- `fileitem`
- `target_path`
- `transfer_type`
- `tmdbid`（可选）
- `doubanid`（可选）
- `download_hash`（可选）
- `downloader`（可选）

这是一轮“最小增强、最大收益”的输入模型收紧，不是新的宿主接入设计。
