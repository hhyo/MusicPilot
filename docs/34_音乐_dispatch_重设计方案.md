# 34. 音乐 dispatch 重设计方案

## 目标

> 当前状态：本方案已经完成第一轮实现与真实宿主验证。音乐 torrent-only 候选当前不再依赖 MoviePilot `/api/v1/download/add` 的影视媒体识别门槛，而是通过宿主 downloader runtime 直接创建真实下载任务；重复 run 时会复用既有 qB 任务。

在保持 `MusicPilot` 现有搜索、订阅、organize、插件 API 边界不变的前提下，重设计音乐下载派发语义，解决当前真实宿主运行态中：

- `real_host_search` 已能返回真实音乐候选
- 下载器已经存在
- 但宿主 HTTP download 语义天然偏影视识别，不适合作为音乐主路径

的问题。

本方案只回答：

1. 为什么当前真实 dispatch 方案不再适合作为音乐主路径。
2. 新的音乐 dispatch 应该落在哪一层。
3. 哪些边界必须保持不变。
4. 第一轮最小实现应改什么，不改什么。

## 当前问题收敛

立项时的真实问题是：

- `real_host_search` 正常
- 宿主下载器存在
- `subscription -> run` 已能进入真实 dispatch
- 当时 `RealDownloadDispatchAdapter` 仍只调用：
  - `/api/v1/download/`
  - `/api/v1/download/add`

其中 `/api/v1/download/add` 的宿主源码语义是：

- 先基于 `torrent_in.title/description` + `tmdbid/doubanid`
- 通过 `MediaChain().recognize_media(...)`
- 成功识别出 **影视** `MediaInfo`
- 再调用 `DownloadChain().download_single(...)`

也就是说，当时这条接口不是“直接提交到下载器”，而是：

**先做影视媒体识别，再决定是否允许添加下载任务。**

这与 MusicPilot 的音乐业务语义不匹配。

## 结论

### 不再适合作为音乐主路径的方案

不再继续把音乐 dispatch 建在：

- MoviePilot `/api/v1/download/add`
- MoviePilot `/api/v1/download/`

这两个宿主 HTTP API 之上。

原因不是它们不能工作，而是它们的入口语义天然要求：

- 影视 `MediaInfo`
- 影视识别成功
- `tmdbid / doubanid / mtype`

这与音乐候选的真实输入模型不一致。

### 推荐的新主路径

音乐 dispatch 改为：

**MusicPilot 负责候选选择与下载请求组装，宿主只负责底层 downloader module 执行。**

也就是复用宿主的下载器底层模块，而不是宿主的影视 download HTTP API。

## 方案对比

### 方案 A：继续沿用 `/api/v1/download/add`，继续补字段

做法：

- 继续给音乐候选补更多识别字段
- 试图提高宿主 `MediaChain().recognize_media(...)` 成功率

优点：

- 改动最少

问题：

- 根问题没有变化，仍然卡在影视识别门槛
- 只会把音乐 dispatch 往影视语义方向继续扭
- 无法形成稳定的音乐下载提交模型

结论：

- 不推荐

### 方案 B：新增音乐专用 downloader dispatch，直接复用宿主 downloader module

做法：

- MusicPilot 直接把候选里的 `enclosure / magnet / title / save_path / downloader` 组装好
- 在宿主插件进程内直接调用下载器模块
- 不再要求先识别影视 `MediaInfo`

优点：

- 语义正确
- 最大限度复用宿主已有下载器接入能力
- 不会把 organize、metadata、search 一起拖进重构

问题：

- 需要新建一条 music dispatch 语义
- 需要自己定义成功/失败和 path handoff 的对接边界

结论：

- 推荐

### 方案 C：完全绕过宿主，MusicPilot 直连 qBittorrent / Transmission

做法：

- MusicPilot 自己维护下载器客户端

优点：

- 最不受宿主现有 download 语义限制

问题：

- 破坏“尽量复用宿主能力”的方向
- 配置、鉴权、运行态、历史回灌都要重做
- 会明显扩大项目维护面

结论：

- 当前不推荐

## 推荐设计边界

### 保持不变

以下边界全部保持不变：

- `metadata/search` 主链
- `charts/discovery` 主链
- `subscription` / scheduler 主链
- `organize preview`
- `organize apply`
- `path_handoff` 和 `history` 的职责边界
- 插件前端 API 路径
- `DispatchService` 的对外调用入口
- `SearchCandidateDetail` / `DispatchResult` 的总体数据结构

### 只替换这一层

只替换：

- `RealDownloadDispatchAdapter.dispatch(...)`

从当前：

- `candidate -> /api/v1/download/add|/api/v1/download/ -> 宿主影视识别 -> 下载器`

改为：

- `candidate -> MusicPilot music dispatch payload -> 宿主 downloader module -> 下载器`

## 新的音乐 dispatch 语义

### 目标语义

对于音乐候选，dispatch 的成功定义应为：

- 下载请求已被真实下载器接受
- 返回可追踪的任务 ID / hash / name

而不是：

- 宿主先识别出影视媒体信息

### 最小输入模型

第一轮只要求以下字段：

- `downloader_id`
- `torrent payload`
  - `enclosure` 或 magnet/content
  - `title`
  - `description`
  - `site_name`
- 可选：
  - `save_path`
  - `labels`

### 第一轮不要求

- `tmdbid`
- `doubanid`
- `mtype`
- 影视 `media_in`

## 推荐落点

### 宿主可复用能力

从宿主源码看，真正可复用的底层能力在下载器模块：

- `QbittorrentModule`
- `TransmissionModule`
- 共同基类 `_DownloaderBase`

这些模块本身已经具备：

- 下载器配置选择
- 路径映射
- `add_torrent(...)`
- 返回 hash / task 标识

### 第一轮推荐落点

第一轮推荐：

- 在 MusicPilot 内新增一个很薄的 `host_downloader_runtime.py`
- 只桥接宿主下载器模块的最小添加任务能力

不要第一轮就做：

- `DownloadChain` 全链复用
- workflow action 接管
- `get_module()` 重载

原因：

- 这些都会把范围拉大
- 当前要解决的是“绕过影视识别门槛”，不是重建整个宿主下载编排

## 对现有代码的影响范围

### 会改

- `backend/app/adapters/download_dispatch.py`
- 可能新增：
  - `backend/app/adapters/host_downloader_runtime.py`
- 相关测试：
  - `backend/tests/test_moviepilot_semantics.py`
  - `backend/tests/test_subscription_execution.py`
  - 可能新增 downloader runtime 定向测试

### 不改

- `backend/app/services/dispatch.py`
- `backend/app/services/subscription_execution.py` 的总体语义
- `backend/app/services/organize.py`
- `backend/app/adapters/organize.py`
- `backend/app/services/host_path_handoff.py`
- 任何前端 API 路径

## 成功标准

第一轮完成后，应该满足：

1. 真实宿主环境下，音乐候选 dispatch 不再因为 `无法识别媒体信息` 被宿主 HTTP download 语义拒绝。
2. 成功标准变成“下载器是否接受任务”，而不是“影视媒体识别是否成功”。
3. `subscription -> run` 在真实下载器已配置时，至少能推进到：
   - `execution_status = dispatched`
   - 且 `dispatch_status` 来自真实下载器提交结果

## 非目标

这轮不做：

- 完整 path handoff 自动化重构
- 下载完成后的自动 organize 重构
- preview / apply 再设计
- 多下载器高级策略
- 直接改宿主源码

## 下一步实施建议

下一步直接进入：

1. 写一份 `music dispatch` 实施 spec
2. 按最小范围替换 `RealDownloadDispatchAdapter`
3. 先验证：
   - 真实下载器任务能否创建
   - 再看后续 `path_handoff/history` 能否继续跟上

一句话总结：

**MusicPilot 现在不需要重设计整个项目，只需要把 dispatch 从“宿主影视识别驱动”切到“宿主下载器执行驱动”。**
