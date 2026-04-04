# 19. organize apply 运行态验证

## 19.1 验证范围

本轮只验证三件事：

1. `RealOrganizeAdapter.apply()` 改成直调 `TransferChain.manual_transfer(...)` 之后，是否真的进入宿主 chain。
2. MusicPilot 的 organize apply 失败回写语义是否仍然稳定。
3. 这次迁移是否没有破坏 `preview`、organize record 查询和插件 API。

本轮不验证：

- `preview` 的宿主内迁移
- `path handoff` 迁移
- `history` 迁移
- 搜索、下载主链路

## 19.2 当前代码层状态

当前代码层迁移已经完成：

- `POST /api/v1/plugin/musicpilot/organize/apply`
- `OrganizeService.apply()`
- `RealOrganizeAdapter.apply()`
- `HostTransferRuntimeBridge.manual_transfer()`
- `TransferChain.manual_transfer(...)`

当前 `apply` 已不再走 `/api/v1/transfer/manual` 的 HTTP 映射。

## 19.3 验证环境

实际使用的路径：

- MusicPilot：`/Users/lihuanhuan/PycharmProjects/MusicPilot`
- 宿主参考源码：`/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot`
- 插件参考仓库：`/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot-Plugins`

验证时区分了三种状态：

1. 宿主源码可导入
2. 宿主本地运行态已初始化
3. 真实宿主 HTTP 服务在线

结论是：

- 宿主源码可导入：`yes`
- 宿主本地运行态已初始化：`no`
- 真实宿主 HTTP 服务在线：`yes`

## 19.4 前置条件检查结论

### 19.4.1 默认参考源码目录不是完整运行态

默认参考源码目录里的数据库文件是：

- `/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/config/user.db`

但它不包含 `systemconfig` 表。

这意味着：

- 本地参考源码目录可以用于“源码阅读”和“直调导入”
- 不能直接视为“已初始化完成的 MoviePilot 运行环境”

### 19.4.2 临时 `CONFIG_DIR` 初始化后仍未补齐运行态

为了避免修改参考仓库，本轮在 MusicPilot 工作区内创建了临时宿主配置目录：

- `/Users/lihuanhuan/PycharmProjects/MusicPilot/.runtime_verification/moviepilot_config`

然后尝试使用宿主自己的数据库初始化逻辑：

- `init_db()`
- `update_db()`

结果：

- `init_db()` 只创建了极少量基础结构，不足以生成 `systemconfig`
- `update_db()` 在当前参考源码下会受宿主运行前置条件影响，出现：
  - `No module named 'app.helper.sites'`
  - `no such table: user`

最终临时数据库里只有 `alembic_version`，仍没有 `systemconfig`。

结论：

- 当前阻塞不是 MusicPilot apply 参数映射问题
- 阻塞点是“本地参考宿主源码目录不等于可直接运行的完整宿主运行态”

## 19.5 apply 直调链路验证结果

### 19.5.1 进入宿主 chain 的结论

本轮已经确认：

- `RealOrganizeAdapter.apply()` 不再发 `/api/v1/transfer/manual` HTTP 请求
- 代码实际进入了 `HostTransferRuntimeBridge`
- 桥接实际执行了宿主侧 `TransferChain().manual_transfer(...)`

失败信息为：

- `manual_transfer_runtime_error:OperationalError:(sqlite3.OperationalError) no such table: systemconfig`

这说明当前失败位置已经在宿主运行态内部，而不是 MusicPilot 的 HTTP 映射层。

### 19.5.2 当前运行态是否跑通

结论：`未跑通`

最后阻塞点：

- 宿主运行态缺少完成 `manual_transfer(...)` 所需的初始化数据库与运行上下文

分类：

- 这是宿主环境问题
- 不是这次 apply 迁移本身的参数映射问题

## 19.6 结果回写与兼容性验证

虽然成功路径还没有在完整宿主运行态下验证通过，但失败路径已经验证：

- `POST /api/v1/plugin/musicpilot/organize/apply` 返回 `503`
- MusicPilot 仍把 organize record 写回为 `failed`
- `failure_reason` 会明确记录：
  - `Host-backed organize apply failed: host_organize_apply_runtime_error:moviepilot_transfer_runtime_failed`

实测 organize record：

- `organize_backend=host`
- `organize_status=failed`
- `integration_point=OrganizeService.apply`
- `capability_source=runtime.seed`

这说明：

- 接入方式虽已从 HTTP 切到宿主直调
- MusicPilot 自己的结果写回语义仍保持稳定

## 19.7 未受影响边界验证

本轮额外验证了以下边界没有被 apply 迁移破坏：

- `POST /api/v1/plugin/musicpilot/organize/preview` 仍可用
- organize record detail 查询仍可用
- `/openapi.json` 仍可访问
- `/docs` 仍可访问
- 插件 API 路径未变化

说明：

- 本轮对 `preview` 的验证只证明“路由和返回结构未被 apply 迁移破坏”
- 不代表本轮同时完成了 `preview` 的真实宿主成功验证

## 19.8 结论

### 已确认

- 代码层迁移：`done`
- 直调入口替换：`done`
- 失败路径写回兼容：`done`
- preview / record / API 未受影响：`done`

### 尚未确认

- “在完整真实宿主运行态中，`TransferChain.manual_transfer(...)` 成功执行并回写 `APPLIED`”

### 当前最后阻塞点

- 缺少一个真正已初始化完成、可被本地直调桥接复用的 MoviePilot 运行环境

### 下一步只需要什么

下一步优先需要的是：

- 正确的宿主本地运行态上下文

而不是：

- 继续改 organize apply 代码结构
- 继续改 preview / path handoff / history

换句话说，本轮结论是：

- 代码迁移已经完成
- 运行态成功验证尚未完成
- 当前更像宿主环境阻塞，而不是 MusicPilot apply 迁移逻辑阻塞
