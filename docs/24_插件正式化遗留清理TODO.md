# 24. 插件正式化遗留清理 TODO

## 目标

把当前为了“本地多仓库验证 / 宿主源码桥接验证”而引入的临时实现收成一份明确 TODO，避免后续把这些验证型 bridge 误当成正式插件运行方案。

本文只记录遗留项，不改变当前实现。

## 当前结论

当前 `organize apply` 的音乐 MVP 已经不再走影视 `TransferChain.manual_transfer(...)`，而是改为：

- MusicPilot 侧生成音乐目标路径
- `HostStorageRuntimeBridge` 复用宿主底层文件/存储操作

当前主路径上的 bridge 已经完成正式化收口：

- 不再依赖本地多仓库路径探测
- 不再使用 `subprocess + python -c`
- 不再通过 `sys.path` 人工注入宿主源码
- 改为宿主进程内直接访问 host `filemanager` 模块

## 一、需要清理的临时 bridge 清单

### 已完成

1. `backend/app/adapters/host_storage_runtime.py`
   - 状态：
     - 已完成正式化
   - 结果：
     - 改成宿主进程内直接调用可用的 file/storage module

2. `plugin_runtime/plugins/musicpilot/adapters/host_storage_runtime.py`
   - 状态：
     - 已同步为正式化后的镜像版本

3. `backend/app/adapters/host_transfer_runtime.py`
   - 状态：
     - 已删除

4. `plugin_runtime/plugins/musicpilot/adapters/host_transfer_runtime.py`
   - 状态：
     - 已删除

### 当前剩余关注点

1. 继续评估 `preview` 是否需要正式插件内接入
2. 继续完善音乐 metadata / layout 层，而不是再回到影视 organize 语义

## 二、需要保留的边界

以下边界后续应继续保持，不属于遗留清理对象：

1. 插件前端 -> MusicPilot 插件 API
   - `POST /api/v1/plugin/musicpilot/organize/preview`
   - `POST /api/v1/plugin/musicpilot/organize/apply`

2. MusicPilot 自己负责的逻辑
   - organize input 解析
   - path handoff 使用
   - 音乐目标路径规划
   - organize record 回写
   - 错误暴露

3. 不在本 TODO 范围内的链路
   - preview
   - path handoff / history
   - search / download

## 三、正式插件实现应替换成什么

### organize apply

当前正式实现：

- `RealOrganizeAdapter.apply()`
- `HostStorageRuntimeBridge.transfer_file(...)`
- 宿主底层文件/存储模块

这部分已完成，不再是待办。

## 四、推荐收敛顺序

1. 继续在正式化后的 `host_storage_runtime.py` 基础上补音乐元数据与命名层
2. 保持 `plugin_runtime` 镜像同步

## 五、完成定义

满足以下条件时，可认为“插件正式化遗留 bridge 清理完成”：

1. `organize apply` 不再依赖：
   - `_resolve_host_root()`
   - `subprocess`
   - `python -c`
   - `sys.path.insert(...)`
2. `host_transfer_runtime.py` 已删除
3. `plugin_runtime` 中不再残留上述 bridge 镜像
4. 运行时不再依赖本地多仓库目录结构

## 六、补充说明

这份 TODO 现在主要作为收口记录保留：

- 它记录了哪些开发期 bridge 已经被清掉
- 也提醒后续不要把音乐 organize 再拉回影视 `manual_transfer(...)` 语义
