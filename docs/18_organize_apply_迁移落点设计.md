# organize apply 迁移落点设计

## 目标

本文只回答一个问题：

- organize apply 如果要做第一轮最小迁移，迁移落点到底应该放在哪里。

本文原本是迁移前设计文档。当前仓库已经按本文结论完成第一轮最小迁移实现：

- `RealOrganizeAdapter.apply()` 不再走 `/api/v1/transfer/manual` HTTP 映射
- 当前改为通过隔离宿主运行时直调 `TransferChain.manual_transfer(...)`
- `preview`、`path handoff`、`history`、插件 API 边界保持不变

当前运行态验证结论见：

- [19_organize_apply_运行态验证.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/19_organize_apply_%E8%BF%90%E8%A1%8C%E6%80%81%E9%AA%8C%E8%AF%81.md)

截至目前：

- 代码层迁移已完成
- `apply` 已不再走 `/api/v1/transfer/manual` HTTP 映射
- 在已初始化的本地 `config-dev` 宿主运行环境下，直调链路已经确认能进入 `TransferChain.manual_transfer(...)`
- 当前仍未补齐的是“成功整理并回写 `APPLIED` 的本地成功样例”；现阶段已确认失败路径语义稳定

本文不讨论：

- preview 迁移
- path handoff 迁移
- history 迁移
- 搜索/下载/历史主链路调整
- 实际代码实现

本文保留前提：

- 插件前端 -> MusicPilot 插件 API 保持不变
- `POST /organize/apply` 保持不变
- 当前 organize 的输入来源层保持不变

> 说明：当前本地工作区没有 `./MoviePilot` 与 `./MoviePilot-Plugins` 目录，本次宿主与插件机制评估基于实际可读的参考路径：
> - `./MoviePilotPkg/MoviePilot`
> - `./MoviePilotPkg/MoviePilot-Plugins`

## 当前 apply 语义拆解

| 项目 | 当前内容 |
| --- | --- |
| apply 当前输入 | `organize_job_id` |
| apply 当前依赖的核心字段 | `candidate/raw_payload`、`binding_id`、`path_handoff`、`host_transfer_source*`、`target_library_path`、`transfer_type` |
| apply 当前宿主调用 | `RealOrganizeAdapter.apply()` -> 隔离宿主运行时 -> `TransferChain.manual_transfer(...)` |
| apply 当前输入组成 | `fileitem`、`target_path`、`transfer_type`、`scrape=false`、`background=false` |
| apply 当前成功语义 | MoviePilot 返回 `success=true`，MusicPilot 映射为 `OrganizeStatus.APPLIED` |
| apply 当前失败语义 | MoviePilot 返回 `success=false` 或请求异常，MusicPilot 映射为 `FAILED` 并记录 `failure_reason` |
| apply 当前写回结果字段 | `organize_backend`、`organize_status`、`strategy`、`strategy_snapshot`、`target_library_path`、`target_relative_path`、`strategy_note`、`integration_point`、`capability_source`、`failure_reason`、`path_handoff`、`verification_state`、`adapter_resolution` |

### 当前 apply 的语义本质

当前 `apply` 做的其实是三件事：

1. 从 MusicPilot 自己的 organize record 和 candidate/binding 上还原 organize 输入。
2. 把 organize 输入映射成 `TransferChain.manual_transfer(...)` 的最小参数。
3. 把宿主返回值重新映射成 MusicPilot organize record 结果。

其中第 2、3 步就是当前最小迁移后仍保留在适配层里的宿主调用映射代码。

## `TransferIntercept` 落点适配表

| 问题 | 结论 |
| --- | --- |
| `TransferIntercept` 在宿主链里的触发时机 | 在真正执行文件/目录整理之前，由 `transhandler` 发出 |
| 它能拿到的输入 | `fileitem`、`mediainfo`、`target_storage`、`target_path`、`transfer_type`、`options` |
| 它能控制的行为 | 可以取消整理，并返回 `source` 和 `reason` |
| 它是否能承接当前 apply 的核心语义 | 不能完整承接 |
| 它承接不了的部分 | 不能作为 organize apply 的入口；不能替代 `manual_transfer`；不能直接返回完整 organize 执行结果；不能负责 MusicPilot 的 record 持久化 |

### 为什么 `TransferIntercept` 不够

`TransferIntercept` 的输出只有：

- `cancel`
- `source`
- `reason`

它的语义是：

- “当宿主已经进入整理流程后，插件是否要拦截/拒绝/放行这次整理”

它不是：

- “插件侧如何发起一次 organize apply”

所以它更像：

- organize apply 迁入宿主后仍然会经过的宿主内拦截点

而不是：

- organize apply 第一轮迁移的最终落点

## apply 迁移保留/下沉表

| 逻辑 | 保留在 MusicPilot 侧 | 下沉到宿主侧 | 说明 |
| --- | --- | --- | --- |
| `organize_job_id` 查找 record | 是 | 否 | 属于 MusicPilot 自己的插件 API 语义 |
| candidate / binding 上下文恢复 | 是 | 否 | 仍属于 MusicPilot 数据层 |
| path handoff 解析 | 是 | 否 | 本轮明确不动 path handoff |
| organize plan / target library path 生成 | 是 | 否 | 当前仍由 MusicPilot organize strategy 负责 |
| organize input 语义组装 | 是，保留语义组装 | 部分下沉，删除 HTTP payload 封装 | `fileitem/target_path/transfer_type` 的语义仍要由 MusicPilot 明确给出 |
| 宿主整理执行 | 否 | 是 | 这是本轮要迁的核心 |
| apply 结果记录 | 是 | 否 | organize record 仍由 MusicPilot 维护 |
| 错误暴露 | 是 | 否 | 失败仍直接暴露到 MusicPilot API |

### 这张表的核心意思

迁移后的变化不是“把 apply 整个交给宿主”。

而是：

- MusicPilot 仍然负责“什么时候执行 apply、输入是什么、结果怎么记账”
- 宿主负责“真正执行 organize apply”

## 备选落点表

| 落点 | 是否适合第一轮 | 为什么 | 风险 |
| --- | --- | --- | --- |
| `TransferIntercept` | 否 | 它是执行前拦截点，不是 apply 入口点 | 承接范围不够，容易设计成半吊子迁移 |
| `TransferChain.manual_transfer` 直调 | 是 | 它与当前 `/api/v1/transfer/manual` 语义一一对应，是最小、最直接的宿主内入口 | 版本耦合会上升，但边界最清楚 |
| `get_module()` | 否 | `get_module()` 面向 `run_module(...)` 重载；`manual_transfer(...)` 本身不是模块方法 | 第一轮容易过度设计，而且落点并不精准 |

### 关键判断

`get_module()` 不适合作为第一轮 organize apply 迁移落点，原因很直接：

1. `get_module()` 用来接管 `run_module(...)` 的模块方法。
2. `TransferChain.manual_transfer(...)` 不是模块方法，而是 `TransferChain` 的公开链路入口。
3. 所以如果第一轮目标只是“把 `/transfer/manual` 的 HTTP 映射层去掉”，最小落点不是 `get_module()`，而是 `TransferChain.manual_transfer(...)` 直调。

## 边界保持表

| 边界 | 必须保持不变的内容 |
| --- | --- |
| 插件 API | `POST /api/v1/plugin/musicpilot/organize/apply` 保持不变 |
| 前端调用 | 前端仍然只提交 `organize_job_id` 到 MusicPilot 插件 API |
| 数据来源 | `source_path` 仍然来自当前 path handoff / history 逻辑，不并入本轮迁移 |
| path handoff | 保持现有主来源/补充来源定义，不动 |
| preview | `POST /organize/preview` 及其 `/transfer/name` 映射不动 |
| 搜索/下载/历史 | 全部不动 |
| organize record | 仍由 MusicPilot 创建、更新和回看 |
| 真实成功链路 | 当前已验证的 host apply 成功语义不能被破坏 |

## 推荐最小落点

### 明确结论

`TransferIntercept` 不足以单独承接第一轮 apply 迁移。

第一轮最小落点应是：

- `TransferChain.manual_transfer(...)` 直调

### 为什么这是最小落点

因为它和当前 HTTP 语义是一一对应的：

- 当前：`RealOrganizeAdapter.apply()` -> `/api/v1/transfer/manual`
- 迁移后：`RealOrganizeAdapter.apply()` -> `TransferChain.manual_transfer(...)`

也就是说，第一轮只替换这一段：

- “插件后端通过 HTTP 请求宿主 organize apply”

变成：

- “插件后端在宿主内直接调用 organize apply 链路入口”

### `TransferIntercept` 在第一轮里的正确位置

它不应该被设计成第一轮 apply 的主落点。

它应该被视为：

- 当 apply 已经迁入 `TransferChain.manual_transfer(...)` 后，宿主内部仍会自然经过的链式拦截点

也就是说：

- 第一轮不需要“把 MusicPilot 迁到 `TransferIntercept` 上”
- 第一轮只需要“让 MusicPilot 的 apply 进入 `TransferChain.manual_transfer(...)`，宿主内原有的 `TransferIntercept` 继续生效”

## 迁移后会变薄或可删除的代码

按这个落点落地以后，最直接变薄的代码是：

1. `RealOrganizeAdapter._build_manual_payload()` 已改成更薄的 `manual_transfer` 参数组装
2. `RealOrganizeAdapter._apply_once()` 中对 `/api/v1/transfer/manual` 的 HTTP 请求组装已删除
3. `RealOrganizeAdapter._build_result()` 保留，但不再依赖 `/transfer/manual` 的 HTTP response 结构

会保留的代码是：

1. `OrganizeService.apply()` 里的 organize record 读取与状态写回
2. `source_path` / organize input 的数据准备
3. MusicPilot 自己的错误暴露和结果持久化

## 最终设计结论

### 1. `TransferIntercept` 是否足够承接第一轮 apply 迁移

不够。

### 2. 如果不够，第一备选落点是什么

第一备选不是别的，而是最推荐的最小落点：

- `TransferChain.manual_transfer(...)` 直调

### 3. 为什么是它

因为它和当前 `/transfer/manual` 的语义最对齐，能把 HTTP 映射层拿掉，但不需要同时重构 preview、path handoff、history 或插件 API。

### 4. 哪些代码迁移后会直接变薄或删除

- `RealOrganizeAdapter._build_manual_payload()`
- `RealOrganizeAdapter.apply()` 里的宿主 HTTP 调用
- 一部分只为 `/transfer/manual` 响应结构存在的映射代码

### 5. 哪些代码即使迁移后也必须留在 MusicPilot 侧

- `organize_job_id -> record` 的查找
- candidate/binding 上下文恢复
- path handoff 解析
- organize plan 生成
- apply 结果记录
- 错误暴露
