# organize apply 成功前提源码分析

## 目标

本文只做一件事：

- 从 MoviePilot 宿主源码中静态分析 `TransferChain.manual_transfer(...)` 成功执行的前提条件。

本文不做：

- 成功样本验证
- preview 迁移
- path handoff / history 迁移
- 搜索/下载链路调整
- 新的策略、fallback、recommendation 抽象

当前分析基线：

- MusicPilot 的 `RealOrganizeAdapter.apply()` 已改为直调 `TransferChain.manual_transfer(...)`
- preview 仍走 `/api/v1/transfer/name`
- path handoff / history / 插件 API 保持不变

## 1. `manual_transfer(...)` 调用路径

### 1.1 入口

宿主入口位于：

- `/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/app/chain/transfer.py:1905`

它分成两条语义分支：

1. 如果显式传入 `tmdbid` 或 `doubanid`
   - 先调用 `MediaChain().recognize_media(...)`
   - 成功后再调用 `do_transfer(...)`
2. 如果没有显式媒体 ID
   - 直接调用 `do_transfer(...)`

### 1.2 主执行链

按当前 MusicPilot 实际输入语义，对应的是第二条分支：

1. `TransferChain.manual_transfer(...)`
2. `TransferChain.do_transfer(...)`
3. `TransferChain.__get_trans_fileitems(...)`
4. `TransferChain.__handle_transfer(...)`
5. `ChainBase.transfer(...)`
6. `FileManager.transfer(...)`
7. `TransHandler.transfer_media(...)`
8. `TransHandler.__transfer_file(...)` / `__transfer_dir(...)`
9. `TransHandler.__transfer_command(...)`

### 1.3 每一步负责什么

| 阶段 | 宿主函数 | 责任 | 是否决定“能不能整理” |
| --- | --- | --- | --- |
| 入口分派 | `manual_transfer(...)` | 判断是否有显式媒体 ID，决定先识别还是直接 `do_transfer` | 否 |
| 输入筛选 | `do_transfer(...)` | 过滤源文件/目录，组装 `TransferTask` | 是，第一道硬门槛 |
| 文件项展开 | `__get_trans_fileitems(...)` | 检查路径存在、目录递归、蓝光目录识别 | 是 |
| 媒体识别 | `__handle_transfer(...)` | 从下载历史或 `MetaInfoPath` 识别 `MediaInfo` | 是，第二道硬门槛 |
| 目标路径确定 | `FileManager.transfer(...)` | 确定 `target_path` / `target_storage` / `transfer_type` | 是 |
| 实际整理 | `TransHandler.transfer_media(...)` | 重命名、目标目录、覆盖模式、拦截事件、执行整理 | 是 |
| 文件操作 | `__transfer_command(...)` | copy/move/link/softlink 或上传/下载 | 是 |

### 1.4 哪一步真正决定“有没有可整理媒体文件”

准确答案是：

- `do_transfer(...)` 中调用 `__get_trans_fileitems(...)` 之后的 `if not file_items`
- 具体源码：
  - `/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/app/chain/transfer.py:1582-1590`

这一步发生在媒体识别之前。

因此：

- `没有找到可整理的媒体文件`

不等价于：

- `未识别到媒体信息`

它更早，表示“源路径经过存在性检查和文件筛选后，没有留下任何可整理文件项”。

## 2. 成功前提条件表

### 2.1 硬前提

| 条件 | 来源 | 说明 |
| --- | --- | --- |
| `fileitem.path` 可由 `StorageChain.get_item(...)` 查到 | `transfer.py:1441-1447` | 路径不存在时直接返回空文件项列表，后续落到“没有找到可整理的媒体文件” |
| 至少存在一个通过筛选的文件项 | `transfer.py:1545-1580` | 过滤规则包含扩展名、大小、隐藏目录、屏蔽词、自定义剧集格式 |
| `MediaInfo` 识别成功 | `transfer.py:1074-1138` | 识别失败会直接返回“未识别到媒体信息” |
| `target_path` 不是现有文件 | `filemanager/__init__.py:433-438` | 否则直接失败 |
| 存在有效目标路径 | `filemanager/__init__.py:440-480` | 当前 MusicPilot 走 `target_path` 分支，因此必须给出有效目录路径 |
| `transfer_type` 有值且受目标存储支持 | `filemanager/__init__.py:481-486` 与 `transhandler.py:396-444` | 本地场景仅支持 `copy/move/link/softlink` |
| 源/目标存储操作对象可用 | `filemanager/__init__.py:488-510` | 否则返回“不支持的存储类型” |

### 2.2 缺了会高概率失败，但不一定立刻失败的条件

| 条件 | 来源 | 说明 |
| --- | --- | --- |
| 文件名/路径可被 `MetaInfoPath(...)` 正确提取媒体要素 | `metainfo.py:70-90`、`media.py:438-459` | 没有显式媒体 ID 时，宿主靠这个识别媒体 |
| 能命中下载历史并回填 `tmdbid/doubanid` | `transfer.py:1618-1635`、`1069-1094` | 命中后会优先走更稳定的 `recognize_media(tmdbid/doubanid)` |
| TV 文件能识别到 `begin_episode` | `transhandler.py:205-218` | TV 场景缺集数会失败 |
| 目标目录可创建 | `transhandler.py:268-281` | `target_oper.get_folder(...)` 失败会中断 |
| 目标文件不存在或覆盖模式允许 | `transhandler.py:283-340`、`763-804` | 否则返回“已存在”或“质量更好/不覆盖” |

### 2.3 配置依赖

| 配置/规则 | 来源 | 作用 | 是否硬前提 |
| --- | --- | --- | --- |
| `settings.RMT_MEDIAEXT` / `RMT_SUBEXT` / `RMT_AUDIOEXT` | `transfer.py:549-555`、`metainfo.py:32-38` | 决定哪些文件算可整理文件、哪些后缀可解析 | 是 |
| `SystemConfigKey.TransferExcludeWords` | `transfer.py:1538-1541` | 命中屏蔽词的文件会被过滤 | 是 |
| `settings.RENAME_FORMAT(...)` | `filemanager/transhandler.py:116-118`、`230-263` | 重命名模板无效会失败 | 是 |
| `settings.SCRAP_FOLLOW_TMDB` | `transfer.py:1142-1149` | 仅影响标题回写，不决定是否可整理 | 否 |

## 3. 失败分支表

| 失败类别 | 触发位置 | 返回语义 | 含义 |
| --- | --- | --- | --- |
| 源路径不存在 | `transfer.py:1441-1445` -> `1588-1590` | `"{name} 没有找到可整理的媒体文件"` | `StorageChain.get_item(...)` 没查到源文件/目录 |
| 全部文件项被过滤掉 | `transfer.py:1545-1580` -> `1588-1590` | `"{name} 没有找到可整理的媒体文件"` | 不是媒体文件、太小、隐藏/回收站、命中屏蔽词、剧集格式不匹配 |
| 媒体识别失败 | `transfer.py:1074-1138` | `"未识别到媒体信息"` | 有可整理文件，但无法得到 `MediaInfo` |
| TV 未识别到集数 | `transhandler.py:205-218` | `"未识别到文件集数"` | 媒体识别到 TV，但 `MetaInfoPath`/格式化后仍没有 episode |
| 目标目录无效 | `filemanager/__init__.py:433-480` | `"不是有效目录"` / `"未找到有效的媒体库目录"` | 目标路径是文件或没有有效整理目录 |
| 整理方式无效 | `filemanager/__init__.py:481-486`、`transhandler.py:396-444` | `"...未设置整理方式"` / `"不支持的整理方式"` | `transfer_type` 缺失或不受支持 |
| 存储不支持 | `filemanager/__init__.py:488-510` | `"不支持的存储类型"` | 源/目标存储无法获取操作对象 |
| 目标目录创建失败 | `transhandler.py:268-281` / `645-648` | `"目标目录 ... 获取失败"` | 无法创建或获取目标目录 |
| 整理被宿主事件拦截 | `transhandler.py:649-665`、`767-784` | `event_data.reason` | `TransferIntercept` 主动取消 |
| 已整理过 | `transfer.py:1605-1616` | `"{name} 已整理过"` | 非 `force` 场景下直接跳过并记失败信息 |
| 目标文件已存在/覆盖规则不允许 | `transhandler.py:283-340`、`785-804` | `"已存在"` / `"质量更好"` / `"不覆盖"` | 命中覆盖规则 |

### 3.1 “没有找到可整理的媒体文件” 的准确含义

准确源码位置：

- `/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/app/chain/transfer.py:1588-1590`

触发前发生了什么：

1. `manual_transfer(...)` 进入 `do_transfer(...)`
2. `do_transfer(...)` 用 `_filter(...)` 调 `__get_trans_fileitems(...)`
3. `__get_trans_fileitems(...)` 会先检查路径是否存在，再展开文件/目录
4. 所有候选项都被过滤掉，或者根本没有有效路径
5. 返回 `False, "{fileitem.name} 没有找到可整理的媒体文件"`

它意味着：

- 这不是媒体识别阶段的错误
- 这是“源输入不满足可整理文件项条件”的错误
- 可能由以下几类原因引起：
  - 源路径不存在
  - 源路径是目录，但目录内没有合规媒体文件
  - 文件后缀不在允许集合里
  - 文件太小
  - 文件在隐藏/回收站目录
  - 命中 `TransferExcludeWords`
  - 自定义剧集格式 `epformat` 不匹配

## 4. 当前 MusicPilot apply 输入对照表

当前 MusicPilot 实际传入：

- `fileitem`
- `target_path`
- `transfer_type`
- `scrape=False`
- `background=False`

具体映射位置：

- `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/organize.py:248-258`
- `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/organize.py:277-298`

| 宿主前提 | 当前 MusicPilot 是否提供 | 结论 |
| --- | --- | --- |
| `fileitem.path` | 提供 | 已满足，但仍取决于该路径在宿主运行态里是否真实存在 |
| `fileitem.storage` | 提供，默认 `local` | 已满足 |
| `fileitem.type` | 提供 | 已满足；若路径存在，宿主会在 `StorageChain.get_item(...)` 时刷新 |
| `fileitem.name/basename/extension/size` | 提供 | 部分满足；若路径存在，宿主同样会刷新这些字段 |
| `target_path` | 提供 | 已满足 |
| `transfer_type` | 提供 | 已满足，前提是该值受目标存储支持 |
| `tmdbid/doubanid/mtype` | 未提供 | 未满足；因此当前不会走“显式媒体 ID 识别”这条更稳定分支 |
| `download_hash/downloader` | 未提供 | 未直接满足；宿主只能尝试按 `fullpath` 反查下载历史 |
| `season/episode_group/epformat` | 未提供 | 对电影通常可省；对 TV 可能成为失败来源 |

### 当前最有可能导致失败的输入缺口

按源码看，当前高概率缺口分两层：

1. **更早的文件项层缺口**
   - `source_path` 在宿主运行态里并不存在
   - 或路径存在，但不满足“可整理文件项”筛选规则

2. **更晚的识别层缺口**
   - 即使文件项筛选通过，当前也没有显式传 `tmdbid/doubanid/mtype`
   - 也没有显式传 `download_hash`
   - 因此宿主只能依赖：
     - `DownloadFiles.fullpath -> download_hash -> DownloadHistory`
     - 或 `MetaInfoPath(path)` 的文件名/目录名识别

### 当前有一个需要注意但不是硬阻塞的点

MusicPilot 当前 `_detect_extension()` 产出的是带点后缀（如 `.mkv`）：

- `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/organize.py:403-407`

而宿主本地 `FileItem.extension` 常规语义是不带点：

- `/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/app/modules/filemanager/storages/local.py:42-52`

不过这在 **源路径真实存在** 的前提下通常不是当前主阻塞，因为：

- `__get_trans_fileitems(...)` 会先 `StorageChain.get_item(fileitem)` 并用宿主自己的 `FileItem` 覆盖输入
- 对应源码：
  - `/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/app/chain/transfer.py:1441-1447`

所以这个差异更像“输入归一不够严谨”，不是当前静态分析里的第一硬门槛。

## 5. 最小 organize apply 输入模型

### 5.1 源码推导的最小输入集合

#### 必填字段

| 字段 | 用途 | 是否当前已具备 |
| --- | --- | --- |
| `source_path` | 让宿主找到真实文件/目录 | 是 |
| `source_storage` | 让 `StorageChain` 选择存储实现 | 是 |
| `source_filetype` | 初始 `FileItem` 语义 | 是 |
| `target_path` | 目标媒体库根路径 | 是 |
| `transfer_type` | 整理方式 | 是 |

#### 至少满足其一的“媒体确认条件”

| 条件类型 | 说明 | 当前是否稳定具备 |
| --- | --- | --- |
| 显式媒体 ID | `tmdbid/doubanid + mtype` | 否 |
| 下载上下文 | `download_hash` 或 `fullpath` 能命中 `DownloadHistory` 并带媒体 ID | 部分具备，但不稳定 |
| 文件名/目录名可识别 | `MetaInfoPath(path)` + `MediaChain().recognize_by_meta(...)` 成功 | 部分具备，但不稳定 |

#### TV 场景额外要求

| 字段/条件 | 说明 | 当前是否稳定具备 |
| --- | --- | --- |
| `begin_episode` 能从路径或 `epformat` 推出 | 否则会失败为“未识别到文件集数” | 否，不稳定 |

### 5.2 可选但能显著提升成功率的字段

| 字段 | 作用 |
| --- | --- |
| `tmdbid` / `doubanid` / `mtype` | 直接绕过纯文件名识别，进入更稳定的显式识别分支 |
| `download_hash` | 稳定命中下载历史，获取媒体 ID、订阅识别词、用户上下文 |
| `downloader` | 与 `download_hash` 组合用于更完整的下载上下文 |
| `season` / `episode_group` / `epformat` | 对 TV 手动整理尤其关键 |

### 5.3 当前可以忽略的字段

| 字段 | 原因 |
| --- | --- |
| `scrape` | 不决定是否进入成功主分支 |
| `background` | 只影响执行方式，不决定是否可整理 |
| `basename/size/modify_time` | 源路径存在时宿主会用真实 `FileItem` 刷新 |

## 6. 输入模型增强落实

基于以上源码分析，当前 MusicPilot 已先做一轮最小输入模型增强，但没有改变 `manual_transfer(...)` 接入落点：

- 新增透传：
  - `tmdbid`
  - `doubanid`
  - `download_hash`
  - `downloader`
- 仍未新增：
  - `mtype`
  - `season`
  - `episode_group`
  - `epformat`

增强原则：

1. 只使用当前 MusicPilot 现有上下文可以稳定恢复的字段。
2. 没有值时不伪造，也不改变现有失败语义。
3. 不改变 preview、path handoff、history 和插件 API 的职责边界。

这意味着后续如果还要继续提高 `manual_transfer(...)` 的成功率，优先级应是：

1. 先验证这四个增强字段对宿主成功分支的提升效果。
2. 再决定是否需要继续补 `mtype` 或 TV 场景字段。
| --- | --- |
| `basename` / `size` / `modify_time` | 若 `source_path` 真实存在，宿主会在 `get_item(...)` 时刷新 |
| `background` | 只决定同步/异步执行方式，不决定是否可整理 |
| `scrape` | 不决定是否能进入成功整理主分支 |

## 6. 分析结论

### 6.1 当前 MusicPilot 输入模型是否理论上足够

结论是：

- **对“偶发成功”来说，理论上足够**
- **对“稳定命中成功分支”来说，还不够**

原因不是当前 adapter 连不上宿主，而是：

1. 当前最低输入模型只保证了“源路径 + 目标路径 + 整理方式”
2. 它没有稳定提供“媒体确认条件”
3. 宿主因此只能依赖：
   - 路径本身能被识别
   - 或按 `fullpath` 命中下载历史

这意味着：

- 当前模型更像“能尝试 organize apply”
- 还不是“稳定可命中宿主成功整理分支”的输入模型

### 6.2 当前看到的失败更像哪一类问题

基于源码，当前出现的：

- `没有找到可整理的媒体文件`

首先指向：

- **文件项层前提未满足**

而不是：

- **媒体识别层失败**

因此在不做实现的前提下，最先要确认的不是“再加什么识别字段”，而是：

1. `source_path` 在宿主运行态里是否真实存在
2. 它是否会通过 `__get_trans_fileitems(...)` 的筛选规则

只有这一步通过以后，才轮得到媒体识别层的输入缺口（`tmdbid/doubanid/download_hash` 等）。

### 6.3 下一步建议

基于源码，下一步应优先判断：

1. 当前失败是 **样本/路径问题**
   - 还是 **输入模型问题**
2. 如果文件项层已经通过但媒体识别仍不稳定
   - 再讨论是否补显式媒体 ID 或下载上下文

因此，后续实现和验收都应以本文的“最小输入模型”作为判断依据，而不是继续从错误消息表面猜测。
