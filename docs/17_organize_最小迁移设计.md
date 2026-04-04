# organize 最小迁移设计

## 目标

本文只讨论 organize 的最小迁移设计，不直接修改实现。

本文关注的是：

- `MusicPilot 插件后端 -> MoviePilot organize 能力` 这一层
- 在不改搜索、下载、历史主路径的前提下，organize 是否值得迁、先迁什么、边界怎么画

本文不包含：

- 立即迁移代码
- 搜索、下载、历史的迁移设计
- 新的 strategy / matrix / fallback 系统
- 插件前端 API 的变更

## organize 当前接入全景

| 项目 | 当前怎么走 | 当前语义 |
| --- | --- | --- |
| organize preview | `POST /api/v1/plugin/musicpilot/organize/preview` -> `OrganizeService.preview()` -> `RealOrganizeAdapter.preview()` -> MoviePilot `/api/v1/transfer/name` | 对明确 `source_path + filetype` 做命名预览 |
| organize apply | `POST /api/v1/plugin/musicpilot/organize/apply` -> `OrganizeService.apply()` -> `RealOrganizeAdapter.apply()` -> MoviePilot `/api/v1/transfer/manual` | 对明确 organize input 执行手动整理 |
| `source_path` | 主来源 `history/download`；补充来源 `history/transfer` | 只负责给 organize 提供输入，不承担 organize 语义 |
| `history/download` 在 organize 中的角色 | 新派发后回读下载记录，提取真实本地路径 | 是新下载 handoff 的主来源 |
| `history/transfer` 在 organize 中的角色 | 历史重放/补充查询 | 不是 organize 主语义，只是补充来源 |
| 为了 HTTP 映射而存在的代码 | `RealOrganizeAdapter._preview_once()`、`_apply_once()`、`_build_manual_payload()`、`_build_result()`、`HostHttpClient` 请求映射、部分 path_handoff 注入逻辑 | 这些代码的存在前提是“organize 通过宿主 HTTP API 接入” |

### 当前 organize 边界的核心事实

1. preview 和 apply 现在都是通过插件 API 暴露给插件前端。
2. preview 的宿主语义是 `/transfer/name`。
3. apply 的宿主语义是 `/transfer/manual`。
4. `source_path` 并不是 organize 能力本身的一部分，而是 organize 的输入来源。
5. 当前最“像补丁”的地方，不是插件 API，而是 `RealOrganizeAdapter` 里围绕 HTTP payload 的映射代码。

## organize 宿主机制位点表

| 宿主位点 | 适合承接什么 organize 语义 | 是否适合做最小迁移第一步 | 风险 |
| --- | --- | --- | --- |
| `TransferRename` | 命名渲染、路径名改写、重命名语义补充 | 否，适合作为第二步或后续精修 | 它只处理“渲染字符串更新”，不足以单独替代整个 preview 接口模型 |
| `TransferIntercept` | 整理前拦截、允许/拒绝整理、对目标路径/整理动作做宿主内控制 | 是，最适合承接 apply 的第一轮迁移 | 它是链路中的拦截点，不是完整 API；如果设计不当会把 MusicPilot 逻辑和宿主流程绑太死 |
| `StorageOperSelection` | 选择源/目标存储操作对象，接入自定义存储能力 | 否，不适合作为第一步单独迁移 | 单独迁它不能解决 preview/apply 主语义，只适合作为 organize 深化后的配套位点 |
| `get_module()` | 重载宿主模块方法，替代部分 filemanager/storage 模块实现 | 否，第一轮不建议 | 覆盖面太大，容易把“最小迁移”变成“宿主模块接管” |
| 宿主模块直调 (`TransferChain` / `StorageChain`) | 直接调用 organize 内部链路和存储能力 | 否，第一轮不建议 | 虽然语义最直接，但版本耦合最高，测试也最重 |

### 设计判断

- 如果只做最小迁移，最合适的 organize 宿主位点不是 `get_module()`，而是围绕 `TransferIntercept` 收缩 apply 语义。
- `TransferRename` 更适合第二步，用来让 preview 更贴近宿主的真实命名链路。
- `StorageOperSelection` 只在未来真的要碰自定义存储或跨存储整理时才有必要一起动。

## organize 迁移候选边界表

| 边界 | 迁 / 不迁 | 原因 |
| --- | --- | --- |
| preview | 暂不作为第一步迁移 | 当前 `/transfer/name` 已经是清晰且较薄的预览语义；先迁它收益有限 |
| apply | 迁 | 它最依赖宿主内部 `TransferChain` / `StorageChain` / `FileItem` / 历史语义，最值得先迁 |
| path handoff | 不迁 | 它属于 organize 输入来源，不属于 organize 宿主能力本身；本轮要保持输入边界稳定 |
| history 查询 | 不迁 | 用户已明确本轮不动历史；而且 history 只是 source_path 来源，不是 organize 主语义 |
| 插件 API | 保持不变 | 用户已明确“插件前端 -> MusicPilot 插件 API”边界不变 |

## organize 迁移收益/代价表

| 项目 | 语义更贴近宿主 | HTTP 映射减少 | 版本耦合增加 | 测试复杂度增加 | 对现有前后端边界影响 | 对当前真实成功链路的风险 |
| --- | --- | --- | --- | --- | --- | --- |
| 只迁 preview | 中 | 中 | 中 | 中 | 小 | 中，preview/apply 可能继续分裂成两种宿主接入方式 |
| 只迁 apply | 高 | 高 | 中到高 | 中 | 小到中 | 可控，前提是插件 API 与 path handoff 保持不变 |
| preview + apply 一起迁 | 高 | 高 | 高 | 高 | 中 | 高，第一轮容易变成 organize 全重写 |
| path handoff 一起迁 | 低 | 低 | 中 | 中 | 会破坏当前边界 | 高，不符合“只迁 organize” |
| history 一起迁 | 低 | 低 | 中 | 中 | 会扩大任务范围 | 高，不符合本轮限制 |

### 设计判断

- “只迁 apply”是收益/代价比最好的第一步。
- “preview + apply 一起迁”从长期看更统一，但不适合第一轮最小迁移。
- path handoff 和 history 一起迁会把 organize 设计任务扩大成“organize + 数据来源重划分”，不该在这轮做。

## organize 最小迁移顺序表

| 顺序 | 动作 | 为什么 |
| --- | --- | --- |
| 第一步 | 只迁 apply 的宿主接入层 | apply 最重、最宿主内聚、最值得减少 HTTP 映射 |
| 第二步 | 评估 preview 是否需要迁到 `TransferRename` 或宿主内命名能力 | 等 apply 稳定后，再决定 preview 是否值得跟进 |
| 暂不动 | path handoff | 它是 organize 输入来源，不是 organize 主语义 |
| 暂不动 | history/download 与 history/transfer | 它们是当前明确的数据来源层，不应在 organize 最小迁移里一起改 |
| 暂不动 | 搜索、下载、插件前端 API | 用户已明确范围外，且这些边界不应被 organize 迁移连带破坏 |

## 推荐最小迁移方案

### 结论

organize 值得迁，但第一轮只建议迁 apply，不建议把 preview、path handoff、history 一起带进去。

### 建议边界

保持不变：

1. 插件前端 -> MusicPilot 插件 API
2. `POST /organize/preview`
3. `POST /organize/apply`
4. path handoff 获取方式
5. `history/download` 和 `history/transfer` 的数据来源职责
6. 搜索、下载、历史的当前接入语义

只替换这一层：

- `MusicPilot 插件后端 -> 宿主 apply 能力`

也就是把当前：

- `RealOrganizeAdapter.apply()` -> `/api/v1/transfer/manual`

设计成下一步可迁为：

- `RealOrganizeAdapter.apply()` -> 宿主 organize 机制位点（优先评估 `TransferIntercept`，必要时再看更贴近的宿主内调用）

### 为什么先迁 apply

1. apply 才是真正承担“整理执行”的宿主语义。
2. apply 当前最依赖 `FileItem`、`StorageChain`、`TransferChain`、`TransferHistory` 等宿主内对象。
3. apply 迁进去后，当前这些代码最有机会自然变薄或可删除：
   - `RealOrganizeAdapter._build_manual_payload()`
   - `RealOrganizeAdapter._apply_once()` 里的 HTTP request/response 组装
   - 一部分“为了配合 `/transfer/manual` payload”而存在的 mapping 代码

### 为什么 preview 不建议第一轮一起迁

1. 当前 `/transfer/name` 已经是一个很薄的 preview 语义。
2. `TransferRename` 更适合处理“宿主命名链中的字符串更新”，不等价于一个独立 preview API。
3. 第一轮同时迁 preview 和 apply，会把“最小迁移”升级成 organize 全量接入改造。

## 第一轮不建议迁移的部分

### 不建议一起迁 path handoff

原因：

- path handoff 不是 organize 语义，是 organize 输入来源
- 把它一起迁会打破当前“接口语义层 / 数据来源层”的清晰边界

### 不建议一起迁 history

原因：

- history 只是读取来源
- 本轮只设计 organize 最小迁移，不该把只读历史查询一并卷进去

### 不建议第一轮用 `get_module()` 全接管

原因：

- `get_module()` 太宽
- 第一轮最容易过度设计
- 应先证明“把 apply 宿主接入层迁进去”本身是否真的降低复杂度

## 迁移前后边界保持说明

迁移前后必须保持不变的边界：

1. 插件前端仍然调用 MusicPilot 插件 API
2. 搜索、下载、历史不动
3. path handoff 仍然由当前数据来源层负责
4. organize record、organize preview/apply 这组插件 API 继续存在

迁移后应该变薄的地方：

1. organize apply 的宿主 HTTP payload 组装
2. organize apply 的宿主 HTTP response 解析
3. 一部分围绕 `/transfer/manual` 的外部映射代码

迁移后不应试图顺手一起动的地方：

1. preview API 语义
2. history 数据来源层
3. search / dispatch / subscription run

## 最终设计结论

### organize 是否值得迁

值得。

### preview / apply / path handoff / history 哪些该迁

- preview：暂不作为第一步迁
- apply：第一步应迁
- path handoff：不迁
- history：不迁

### 如果只做一轮最小迁移，第一步具体迁什么

- 只迁 organize apply 的宿主接入层

### 迁移后哪些现有代码会变薄或可删除

- `RealOrganizeAdapter.apply()` 的 HTTP 映射代码
- `RealOrganizeAdapter._build_manual_payload()`
- 一部分“为了配合 `/transfer/manual` 请求体而存在”的外部字段拼装逻辑

### 哪些边界必须保持不变

- 插件前端 API 不变
- 搜索/下载/历史不动
- 当前真实成功链路不破坏
- path handoff 仍留在数据来源层，不并入 organize 迁移第一步
