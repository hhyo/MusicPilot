# MusicTransferChain 重构实施计划

## 目标

把 `MusicTransferChain.process()` 从“仅续跑 pending handoff”重构为完整的下载整理主链，对齐 MoviePilot `TransferChain.process()` 的组织方式。

## 范围

- `backend/app/chain/transfer.py`
- `backend/app/db/acquisition_oper.py`
- `backend/app/db/orchestration_oper.py`
- `backend/app/startup/scheduler.py`
- `backend/tests/`
- `plugin_runtime/plugins/musicpilot/`

## 实施步骤

### 1. 先补失败测试

锁定以下行为：

- 新 binding 会被 `process()` 扫描
- 缺少 organize record 时会自动创建 preview
- 具备 source path 时自动 apply
- 未具备 source path 时转入 `pending_history_sync`
- pending record 命中路径后自动 apply
- pending record 超时后标记 unresolved

### 2. 补查询能力

在 oper 层补齐：

- 列出待 transfer binding
- 按 binding 查 organize record
- 过滤已完成/未完成 organize 状态

### 3. 重写 `MusicTransferChain.process()`

内部拆成：

- `_scan_transfer_candidates()`
- `_process_transfer_binding()`
- `_ensure_preview_record()`
- `_auto_apply_preview()`
- `_reconcile_pending_records()`

### 4. 收口状态回写

保证 binding / organize record / subscription run 三处状态一致：

- preview 创建
- apply 成功
- pending
- unresolved
- failed

### 5. 同步 runtime mirror

把主仓 transfer chain 和相关 oper、scheduler 改动同步到：

- `plugin_runtime/plugins/musicpilot/`

### 6. 全量验证

至少执行：

- transfer 定向测试
- organize / subscription 相关回归
- backend 全量
- `python3 scripts/package_plugin.py`

## 完成定义

只有满足以下条件才算完成：

- `process()` 具备扫描新 binding 的能力
- `process()` 不再只是 pending reconcile 包装层
- `music-transfer` 调度入口驱动完整下载整理主链
- runtime mirror 同步
- 测试和打包通过
