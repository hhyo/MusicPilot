# 22. organize apply 增强输入效果验证

## 目标

本轮只验证一件事：

- `tmdbid / doubanid / download_hash / downloader` 四个增强字段，是否真的对 `TransferChain.manual_transfer(...)` 的宿主执行分支产生了影响。

本轮不做：

- 成功样本验收
- preview 迁移
- path handoff / history 职责调整
- 搜索 / 下载链路调整
- 新的策略、fallback、recommendation 抽象

## 1. 增强字段注入路径

| 字段 | MusicPilot 来源 | 进入宿主的位置 |
| --- | --- | --- |
| `tmdbid` | `candidate.raw_payload.host_media_reference.tmdbid`，其次 `host_context.media_info.tmdb_id` | `TransferChain.manual_transfer(tmdbid=...)` |
| `doubanid` | `candidate.raw_payload.host_media_reference.doubanid`，其次 `host_context.media_info.douban_id` | `TransferChain.manual_transfer(doubanid=...)` |
| `download_hash` | `candidate.raw_payload.path_handoff.download_hash` | `TransferChain.manual_transfer(download_hash=...)` |
| `downloader` | `binding.target_downloader` 注入到 `candidate.raw_payload.host_transfer_downloader` | `TransferChain.manual_transfer(downloader=...)` |

代码层验证已由单元测试覆盖：

- `backend/tests/test_moviepilot_semantics.py`
- `backend/tests/test_organize_integration.py`

## 2. 宿主源码命中点

| 字段 | 宿主命中点 | 影响 |
| --- | --- | --- |
| `tmdbid` / `doubanid` | `app/chain/transfer.py:1938-1963` | 命中显式媒体 ID 分支，先 `recognize_media(...)` 再 `do_transfer(...)` |
| `download_hash` | `app/chain/transfer.py:1619-1634` | 在 `do_transfer(...)` 里优先按 hash 查询 `DownloadHistory` |
| `downloader` | `app/chain/transfer.py:1680-1682` | 作为 `TransferTask` 上下文补充，不是第一硬门槛 |

与 `mtype` 直接相关的宿主源码位置：

- `app/modules/themoviedb/__init__.py:122-138`
- `app/modules/themoviedb/__init__.py:514-520`

当 `tmdbid` 存在但 `mtype` 为空，且同一个 `tmdbid` 可能同时对应电影和电视剧时，宿主会走到：

- `无法判断tmdb_id:{tmdbid} 是电影还是电视剧`
- `tmdb_id:{tmdbid} 无法确定媒体类型，识别失败`

## 3. 本轮诊断样本上下文

本轮没有重新设计新样本，而是沿用当前运行态分析里已有的 Matrix 文件名样本，做“带增强字段 / 不带增强字段”的源码级对照诊断。

| 项目 | 当前值 |
| --- | --- |
| `source_path` | `/downloads/The.Matrix.1999.1080p.WEB-DL.mkv` |
| `fileitem.storage` | `local` |
| `fileitem.type` | `file` |
| `target_path` | `/tmp/musicpilot-organize-target` |
| `transfer_type` | `copy` |
| `tmdbid` | `603` |
| `doubanid` | `1291843` |
| `download_hash` | `stub-download-001` |
| `downloader` | `QB` |

额外运行态事实：

- 本地样本路径 `/downloads/The.Matrix.1999.1080p.WEB-DL.mkv` 当前并不存在
- 本地宿主 `config-dev/user.db` 中：
  - `downloadhistory` 为空
  - `downloadfiles` 为空

这意味着本轮只能验证“字段是否命中宿主分支”，不能用它来证明 `download_hash` 已经命中真实下载历史。

## 4. 带增强字段 / 不带增强字段对照结果

### 4.1 不带增强字段

诊断脚本观测到：

```json
{
  "label": "without_enhancement",
  "state": false,
  "message": "The.Matrix.1999.1080p.WEB-DL.mkv 没有找到可整理的媒体文件",
  "events": [
    {
      "event": "do_transfer",
      "has_mediainfo": false,
      "download_hash": null,
      "downloader": null
    }
  ]
}
```

结论：

- 没有命中显式媒体 ID 分支
- 直接进入 `do_transfer(...)`
- 最终停在文件项筛选为空这一层

### 4.2 带增强字段

诊断脚本观测到：

```json
{
  "label": "with_enhancement",
  "state": false,
  "message": "媒体信息识别失败，tmdbid：603，doubanid：1291843，type: None",
  "events": [
    {
      "event": "recognize_media",
      "kwargs": {
        "tmdbid": "603",
        "doubanid": "1291843",
        "mtype": "None",
        "episode_group": "None"
      }
    }
  ]
}
```

结论：

- `tmdbid / doubanid` 确实进入了宿主 `manual_transfer(...)`
- 它们已经把执行路径从“直接 `do_transfer(...)`”推进到了“先 `recognize_media(...)` 的显式媒体 ID 分支”
- 当前失败已经从“文件项筛选为空”前移为“显式媒体识别失败”

## 5. 失败阶段判定

| 场景 | 当前失败阶段 | 依据 |
| --- | --- | --- |
| 不带增强字段 | 文件项筛选阶段 | 返回 `没有找到可整理的媒体文件`，且事件只有 `do_transfer(...)` |
| 带增强字段 | 媒体识别阶段 | 返回 `媒体信息识别失败...type: None`，且事件先进入 `recognize_media(...)` |

这说明：

- 增强字段是有效的
- 失败分支已经后移
- 但后移的主因是 `tmdbid / doubanid`
- `download_hash / downloader` 在当前样本里尚未发挥作用，因为：
  1. 当前样本路径不存在
  2. 本地宿主下载历史为空
  3. 显式 ID 分支已在更早阶段因为 `mtype=None` 失败，根本还没进入 `do_transfer(...)`

## 6. 是否需要最小日志增强

当前结论已经足够清楚，因此本轮不需要再改代码补日志。

原因：

1. 代码层已有单元测试，证明四个字段已经进入 bridge / adapter 调用层。
2. 一次性源码级诊断脚本已经证明：
   - 显式媒体 ID 分支被触发
   - 不带增强字段时仍是原来的文件项筛选分支
3. 当前剩余问题不是“看不见”，而是“宿主下载历史为空 + `mtype` 为空”。

## 7. 本轮结论

### 已确认

- `tmdbid / doubanid` 已经真正进入宿主 `manual_transfer(...)`
- 它们已经推动宿主从“文件项筛选分支”转到“显式媒体识别分支”
- 当前失败后移到了媒体识别阶段

### 尚未确认

- `download_hash / downloader` 在真实下载历史命中场景下是否能进一步提升成功率

不是因为它们没有传进去，而是因为当前本地宿主运行态里没有对应 `downloadhistory/downloadfiles` 记录。

### 下一步最值钱的判断

如果只做下一轮最小增强，**最值得补的是 `mtype`**，不是继续扩其它字段。

理由：

1. 当前运行态日志已经明确指向：
   - `无法判断tmdb_id:603 是电影还是电视剧`
   - `tmdb_id:603 无法确定媒体类型，识别失败`
2. 这说明增强字段已经起效，当前新阻塞点就是缺少宿主可直接理解的媒体类型。
3. 但需要诚实保留一个前提：
   - 即便补了 `mtype`，当前样本的 `source_path` 不存在、下载历史为空，后续仍可能重新落回文件项层问题。

所以准确结论是：

- 下一步最值钱的字段增强：`mtype`
- 但它不是“保证成功”的充分条件
- 它只是当前已被源码和运行态共同指向的下一个最小输入缺口
