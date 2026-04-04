# 24. 插件正式化遗留清理 TODO

## 目标

把当前为了“本地多仓库验证 / 宿主源码桥接验证”而引入的临时实现收成一份明确 TODO，避免后续把这些验证型 bridge 误当成正式插件运行方案。

本文只记录遗留项，不改变当前实现。

## 当前结论

当前 `organize apply` 的音乐 MVP 已经不再走影视 `TransferChain.manual_transfer(...)`，而是改为：

- MusicPilot 侧生成音乐目标路径
- `HostStorageRuntimeBridge` 复用宿主底层文件/存储操作

但这条链路仍然带有明显的“开发期本地桥接”痕迹，不符合最终插件运行规范。

## 一、需要清理的临时 bridge 清单

### P0：正式插件实现前必须移除

1. `backend/app/adapters/host_storage_runtime.py`
   - 当前问题：
     - 通过 `_resolve_host_root()` 猜测本地 `MoviePilot` / `MoviePilotPkg/MoviePilot` 路径
     - 通过 `subprocess + python -c` 启动隔离解释器
     - 通过 `sys.path.insert(0, host_root)` 人工注入宿主源码
   - 为什么不合规：
     - 正式插件运行时不应依赖工作区多仓库目录结构
     - 插件应直接运行在宿主进程内，而不是额外开一个 Python 解释器
   - 后续动作：
     - 改成宿主进程内直接调用可用的 file/storage module

2. `plugin_runtime/plugins/musicpilot/adapters/host_storage_runtime.py`
   - 当前问题：
     - 与主仓库同样的本地 bridge 逻辑被镜像到了 runtime
   - 后续动作：
     - 等主仓库替换为正式插件接入后同步移除 bridge 版实现

### P0：目前已不再是主路径，但仍属于历史验证代码

3. `backend/app/adapters/host_transfer_runtime.py`
   - 当前状态：
     - 不再作为当前 `organize apply` 主路径
     - 只剩历史验证价值
   - 当前问题：
     - 同样依赖 `_resolve_host_root()`、`subprocess`、`sys.path` 注入
   - 后续动作：
     - 若 preview / 其它链路不再需要这类直调验证，直接删除

4. `plugin_runtime/plugins/musicpilot/adapters/host_transfer_runtime.py`
   - 当前状态：
     - mirror 历史验证代码
   - 后续动作：
     - 与主仓库同步删除

### P1：宿主源码桥接里的临时兼容 hack

5. `sys.modules.setdefault("app.helper.sites", ...)` 这类 stub
   - 出现位置：
     - `host_storage_runtime.py`
     - `host_transfer_runtime.py`
   - 当前问题：
     - 这是为了让参考源码目录可导入而加的临时兜底
   - 后续动作：
     - 正式插件实现中必须删除

6. `_resolve_host_root()` 路径探测规则
   - 当前问题：
     - 假设宿主源码在 `../MoviePilot` 或 `../MoviePilotPkg/MoviePilot`
   - 后续动作：
     - 正式插件运行时不再需要路径探测

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

当前临时 bridge：

- `RealOrganizeAdapter.apply()`
- `HostStorageRuntimeBridge.transfer_file(...)`
- 宿主底层文件/存储模块

正式版目标：

- `RealOrganizeAdapter.apply()`
- 宿主进程内可直接访问的 file/storage module
- 不再经过：
  - `_resolve_host_root()`
  - `subprocess`
  - `python -c`
  - `sys.path` 注入

### host transfer runtime

当前状态：

- 已不是主路径

正式版目标：

- 若后续没有正式用途，直接删除
- 不再保留“为了本地源码验证而存在”的 runtime bridge

## 四、推荐收敛顺序

1. 先替换 `host_storage_runtime.py`
   - 这是当前 `organize apply` 主路径上的临时 bridge

2. 再删除 `host_transfer_runtime.py`
   - 当前它已经不是主路径，更像历史验证残留

3. 最后同步清掉 `plugin_runtime` 镜像中的同类文件

## 五、完成定义

满足以下条件时，可认为“插件正式化遗留 bridge 清理完成”：

1. `organize apply` 不再依赖：
   - `_resolve_host_root()`
   - `subprocess`
   - `python -c`
   - `sys.path.insert(...)`

2. `host_storage_runtime.py` 被替换或删除

3. `host_transfer_runtime.py` 被删除，或明确只保留在非运行时验证工具里

4. `plugin_runtime` 中不再残留上述 bridge 镜像

5. 运行时不再依赖本地多仓库目录结构

## 六、补充说明

这份 TODO 的作用是防止后续遗漏，不表示当前实现无效。

当前 bridge 实现仍有现实价值：

- 它帮助验证了宿主底层能力是否可复用
- 它帮助确认了影视 organize 语义与音乐 organize 语义不一致

但它的定位应该明确为：

- 开发期验证实现
- 不是最终插件规范实现
