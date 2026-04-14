# MusicTransferChain 对齐 MoviePilot 设计

## 目标

把 MusicPilot 的下载后整理闭环重构成与 MoviePilot `TransferChain` 同构的主链实现。

完成后：

- `MusicTransferChain.process()` 成为唯一后台整理入口
- `process()` 主动扫描待整理下载，而不是只处理 `pending_history_sync`
- `preview / apply / retry / rebuild_preview / repair_source_path` 统一收口到 `MusicTransferChain`
- 宿主调度只需要调用 `music-transfer`

## 背景

当前 `MusicTransferChain` 已经具备：

- `preview`
- `apply`
- `retry`
- `rebuild_preview`
- `repair_source_path`
- `reconcile_pending_once`

但 `process()` 仍然只是 `reconcile_pending_once()` 的别名，缺少 MoviePilot `TransferChain.process()` 的核心语义：

- 扫描新完成下载
- 建立整理作业
- 自动推进 organize preview/apply
- 统一回写 binding / organize record / subscription run 状态

## 对齐目标

### MoviePilot 对齐点

参考 MoviePilot：

- 调度入口直接触发 `TransferChain.process()`
- `process()` 扫描待整理对象
- 整理链内部统一推进作业/任务状态
- 整理失败与重试都收口在一条链里

MusicPilot 也应保持同构：

- 调度入口：`startup/scheduler.py -> run_transfer_once() -> MusicTransferChain.process()`
- 主编排：`chain/transfer.py`
- 数据回写：`db/acquisition_oper.py`、`db/orchestration_oper.py`
- 宿主底层能力：`modules/path_handoff.py`、`modules/organize.py`、`modules/host_storage_runtime.py`

### 明确不对齐的点

不直接复用 MoviePilot 影视语义或内部实现：

- 不复用影视 `TransferTask / TransferJob / MediaInfo / MetaBase`
- 不复用宿主内部 `DownloadHistoryOper / TransferHistoryOper`
- 不复制目录监控逻辑

MusicPilot 维持自己的音乐领域语义：

- `MusicMediaInput -> MusicMetaBase -> MusicMediaInfo`
- organize plan 为音乐目录规划
- organize apply 通过宿主文件/存储底层执行

## 新的主链设计

### 顶层入口

`MusicTransferChain` 保留以下公开动作：

- `process(now=None) -> dict`
- `preview(payload, subscription_run_id=None) -> OrganizePreviewResult`
- `apply(payload) -> OrganizePreviewResult`
- `retry(record_id) -> OrganizePreviewResult`
- `rebuild_preview(record_id) -> OrganizePreviewResult`
- `repair_source_path(record_id) -> OrganizePreviewResult`
- `list_records(...) -> OrganizeRecordListData`
- `get_record(record_id) -> OrganizePreviewResult`

其中 `process()` 是后台整理主入口。

### `process()` 的两阶段结构

#### Phase A：扫描新下载 binding

新增内部阶段：

- `_scan_transfer_candidates()`
- `_process_transfer_binding(binding, now)`
- `_ensure_preview_record(binding, now)`
- `_auto_apply_preview(record, now)`

目标：

- 找到已经派发、具备候选与媒体上下文、但尚未建立 organize record 的 binding
- 为其创建 organize preview
- 如果已经具备明确本地源路径，则立即自动 apply
- 如果还没有源路径，则转入 `pending_history_sync`

#### Phase B：续跑 pending handoff

保留当前续跑逻辑，但下沉为 `process()` 的第二阶段：

- `_reconcile_pending_records(now)`

目标：

- 对已有 `pending_history_sync` organize record 继续从宿主下载历史回读路径
- 一旦命中真实路径，自动 apply
- 超过 TTL 未命中则标记 `handoff_unresolved`

### 结果对象

`process()` 返回结构化结果，替代当前仅偏向 pending handoff 的返回：

- `processed_binding_ids`
- `created_record_ids`
- `applied_record_ids`
- `pending_record_ids`
- `unresolved_record_ids`
- `failed_record_ids`
- `skipped_binding_ids`
- `diagnostics`

兼容当前 dashboard / scheduler 摘要需要的计数信息：

- `summary.created`
- `summary.applied`
- `summary.pending`
- `summary.unresolved`
- `summary.failed`
- `summary.skipped`

## 状态推进规则

### Binding

binding 侧长期语义固定为：

- `host_submitted`
- `transfer_pending`
- `pending_history_sync`
- `handoff_resolved`
- `handoff_unresolved`
- `organize_preview_ready`
- `organize_applied`
- `organize_failed`

### Organize record

organize record 保持：

- `planned`
- `preview_ready`
- `apply_pending`
- `applied`
- `failed`
- `skipped`

### Subscription run

订阅执行侧需要同步回写：

- `organize_preview_id`
- `organize_status`
- `path_handoff_status`
- `path_handoff_source`
- `resolved_source_path`
- `error_message`

## 持久化与查询

为支持 `process()` 主动扫描，查询边界需要补齐：

- acquisition 侧：
  - 列出待 transfer 的 binding
  - 读取 binding 对应 candidate / job / task 状态
- orchestration 侧：
  - 按 binding 查 organize record
  - 列出 pending handoff record

不新增 `Service`；所有新增查询放到：

- `db/acquisition_oper.py`
- `db/orchestration_oper.py`

## 与 organize module 的边界

`modules/organize.py` 继续作为底层 adapter 边界：

- preview：MusicPilot 本地音乐目录规划
- apply：宿主文件/存储执行

但主流程编排只允许存在于 `MusicTransferChain`。

## 调度与启动

调度保持：

- `music-transfer`

入口保持：

- `startup/scheduler.py -> run_transfer_once()`

变化点只有：

- `run_transfer_once()` 调用的 `process()` 将从“仅续跑 pending”升级为“完整 transfer 主链”

## 测试要求

本次重构至少新增以下测试覆盖：

1. `process()` 能为新 binding 建立 organize preview
2. `process()` 在已有真实 source path 时自动 apply
3. `process()` 在缺少 source path 时写入 `pending_history_sync`
4. `process()` 能续跑 pending record 并在命中路径后 apply
5. `process()` 超过 TTL 后写入 `handoff_unresolved`
6. `music-transfer` 调度入口继续调用 `MusicTransferChain.process()`

## 验收标准

满足以下条件才算完成：

1. `MusicTransferChain.process()` 不再只是 `reconcile_pending_once()` 的别名
2. 新下载 binding 不依赖其他链显式触发，也能进入 organize preview/apply
3. pending handoff 续跑只是 `process()` 的一个阶段
4. organize 相关手动动作仍可用且行为不回退
5. backend 定向测试、全量测试、打包全部通过
6. `plugin_runtime` 后端镜像同步一致
