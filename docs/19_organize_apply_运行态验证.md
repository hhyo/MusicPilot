# 19. organize apply 运行态验证

> 历史记录：本文记录的是早期 `manual_transfer(...)` 直调迁移实验的运行态验证结果。当前仓库中的 `organize apply` 已经不再走 `TransferChain.manual_transfer(...)`，而是改为通过宿主底层 file/storage transfer runtime 执行音乐文件整理。

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

## 19.2 当时的代码层状态

当时的代码层迁移已经完成：

- `POST /api/v1/plugin/musicpilot/organize/apply`
- `OrganizeService.apply()`
- `RealOrganizeAdapter.apply()`
- `HostTransferRuntimeBridge.manual_transfer()`
- `TransferChain.manual_transfer(...)`

当时的 `apply` 已不再走 `/api/v1/transfer/manual` 的 HTTP 映射。

## 19.3 验证环境

实际使用的路径：

- MusicPilot：`/Users/lihuanhuan/PycharmProjects/MusicPilot`
- 宿主参考源码：`/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot`
- 插件参考仓库：`/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot-Plugins`

验证时区分了三种状态：

1. 宿主源码可导入
2. 宿主本地运行态已初始化
3. 真实宿主 HTTP 服务在线

本轮最终使用的本地运行环境是：

- 宿主源码根目录：`/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot`
- 宿主本地开发配置目录：`/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/config-dev`
- 本地宿主服务端口：`3001`

结论是：

- 宿主源码可导入：`yes`
- 宿主本地运行态已初始化：`yes`
- 真实宿主 HTTP 服务在线：`yes`

## 19.4 前置条件检查结论

### 19.4.1 默认 `config/` 不是完整运行态

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

- 当前阻塞不再是 MusicPilot apply 参数映射问题
- 也不再是“宿主本地运行态完全缺失”
- 真实可用的本地运行目录是 `config-dev/`，不是仓库内默认的 `config/`

### 19.4.3 已切换到可用的本地宿主运行态

按宿主 README / `docs/local-development.md` 的方式，本轮确认：

- `config-dev/user.db` 已存在
- 其中包含 `systemconfig`、`user`、`downloadhistory`、`transferhistory` 等关键表
- 本地 MoviePilot 进程已在 `3001` 端口监听
- `app/helper/sites.cpython-312-darwin.so` 等本地资源已到位

因此，本轮后续验证均以：

- `CONFIG_DIR=/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/config-dev`

作为宿主运行态上下文。

## 19.5 apply 直调链路验证结果

### 19.5.1 进入宿主 chain 的结论

本轮已经确认：

- `RealOrganizeAdapter.apply()` 不再发 `/api/v1/transfer/manual` HTTP 请求
- 代码实际进入了 `HostTransferRuntimeBridge`
- 桥接实际执行了宿主侧 `TransferChain().manual_transfer(...)`

在可用 `config-dev` 环境下，`HostTransferRuntimeBridge.manual_transfer()` 已经返回了宿主业务语义结果，而不是环境初始化错误：

- `{'success': False, 'organize_status': 'failed', 'message': 'The.Matrix.1999.1080p.WEB-DL.mkv 没有找到可整理的媒体文件'}`

这说明：

- 直调已经真正进入 `TransferChain.manual_transfer(...)`
- 当前失败位置已经是宿主 organize 业务语义层
- 不再是 `systemconfig` 之类的环境初始化错误

### 19.5.2 当前运行态是否跑通

结论：`直调链路已跑通到宿主业务层，但当前成功样例未跑通`

当前最后阻塞点：

- 本轮用于验证的样本文件 `The.Matrix.1999.1080p.WEB-DL.mkv` 被宿主判定为“没有找到可整理的媒体文件”

分类：

- 这是宿主业务识别/样本问题
- 不是环境初始化问题
- 也不是这次 apply 迁移的接入层问题

## 19.6 结果回写与兼容性验证

虽然成功路径还没有在本地宿主运行态下验证通过，但失败路径已经验证：

- `POST /api/v1/plugin/musicpilot/organize/apply` 返回 `200`
- 返回体里的 organize 结果为 `organize_status=failed`
- MusicPilot 仍把 organize record 写回为 `failed`
- `failure_reason` 会明确记录宿主业务错误：
  - `The.Matrix.1999.1080p.WEB-DL.mkv 没有找到可整理的媒体文件`

实测 organize record：

- `organize_backend=host`
- `organize_status=failed`
- `integration_point=RealOrganizeAdapter.apply.moviepilot_transfer_chain_manual_transfer`
- `capability_source=moviepilot.runtime.transfer.manual_transfer`

这说明：

- 接入方式已从 HTTP 切到宿主直调
- MusicPilot 自己的结果写回语义仍保持稳定
- 当宿主返回业务失败时，插件 API 仍保持 `200 + failed result` 的当前语义，不会误报成 transport error

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

## 19.8 历史结论

### 当时已确认

- 代码层迁移：`done`
- 直调入口替换：`done`
- 在已初始化本地宿主运行态中进入 `TransferChain.manual_transfer(...)`：`done`
- 失败路径写回兼容：`done`
- preview / record / API 未受影响：`done`

### 当时尚未确认

- “在本地真实宿主运行态中，`TransferChain.manual_transfer(...)` 成功执行并回写 `APPLIED`”

### 当时最后阻塞点

- 还缺一个会被宿主成功识别并完成整理的本地样本

### 当时判断的下一步

下一步优先需要的是：

- 更合适的本地 organize 输入样本

而不是：

- 继续改 apply 接入层
- 继续改 preview / path handoff / history

换句话说，当时这轮的结论是：

- `manual_transfer(...)` 直调迁移已经完成
- 运行态前置环境已经满足
- 直调链路已经进入宿主 organize 业务层
- 当时未完成的是“成功样例验证”，不是接入层打通

## 19.9 当前状态说明

当前仓库已经不再以这条影视 `manual_transfer(...)` 路径作为 `organize apply` 主实现。

当前主实现改为：

- MusicPilot 负责音乐 organize input 解析、目标路径规划与 record 回写
- 宿主仅复用底层 file/storage transfer 能力执行文件整理

对应说明见：

- [23_音乐文件整理技术设计与实现方案.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/23_%E9%9F%B3%E4%B9%90%E6%96%87%E4%BB%B6%E6%95%B4%E7%90%86%E6%8A%80%E6%9C%AF%E8%AE%BE%E8%AE%A1%E4%B8%8E%E5%AE%9E%E7%8E%B0%E6%96%B9%E6%A1%88.md)
- [24_插件正式化遗留清理TODO.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/24_%E6%8F%92%E4%BB%B6%E6%AD%A3%E5%BC%8F%E5%8C%96%E9%81%97%E7%95%99%E6%B8%85%E7%90%86TODO.md)
