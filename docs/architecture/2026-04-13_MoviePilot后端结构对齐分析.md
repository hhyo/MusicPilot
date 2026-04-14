# MoviePilot 后端结构对齐分析

> 用途：基于当前 MoviePilot 仓库真实代码结构，梳理其目录、命名、分层、主流程编排方式，并给出 MusicPilot 后端的同构目标。本文强调“等价职责严格对齐”，不是“表面有 Chain 即算对齐”。

## 1. 结论

如果要让 MusicPilot 后端与 MoviePilot 完全对齐，必须同时对齐四件事：

1. 目录结构
2. 文件命名
3. 主流程编排入口
4. 支撑层分层方式

只补 `Music*Chain` 而不重排目录和支撑层，结果仍然会是旧项目加一层 facade，不算同构。

## 2. MoviePilot 当前后端真实结构

基于当前仓库快照，MoviePilot 的 `app/` 目录包含这些一级能力目录：

- `api/`
- `chain/`
- `core/`
- `db/`
- `helper/`
- `modules/`
- `plugins/`
- `schemas/`
- `startup/`
- `utils/`
- `workflow/`
- `agent/`

其中对 MusicPilot 当前后端主重构最有直接参考价值的是：

- `api/endpoints/`
- `chain/`
- `core/`
- `db/models/`
- `db/*_oper.py`
- `helper/`
- `modules/`
- `schemas/`
- `startup/`
- `utils/`

`plugins/`、`workflow/`、`agent/` 在 MusicPilot 里只有出现等价职责时才需要引入，不应为了“像”而创建空壳目录。

## 3. MoviePilot 的命名与目录语义

### 3.1 API 目录不是 `routes/`，而是 `api/endpoints/`

MoviePilot 当前 endpoint 文件名是领域名，而不是技术层名或资源中间态名，例如：

- `media.py`
- `search.py`
- `download.py`
- `transfer.py`
- `subscribe.py`
- `dashboard.py`

这说明它的 API 命名原则是：

- 以业务领域命名
- 以主链语义命名
- 不以中间资源实现细节命名

对应到 MusicPilot：

- `jobs.py` 应收进 `search.py`
- `downloads.py` 应收进 `download.py`
- `subscriptions.py` 应收进 `subscribe.py`
- `organize.py` 应收进 `transfer.py`
- `charts.py` 应收进 `chart.py`

### 3.2 主流程目录不是 `services/`，而是 `chain/`

MoviePilot 当前 `app/chain/` 下有 21 个具体 chain 文件，加上 `ChainBase`：

- `media.py`
- `search.py`
- `download.py`
- `transfer.py`
- `subscribe.py`
- `dashboard.py`
- 以及 `site.py`、`storage.py`、`workflow.py` 等其他领域链

这说明 MoviePilot 的主流程组织原则不是“service 调 service”，而是：

- endpoint 直接调 chain
- scheduler 直接调 chain
- monitor 直接调 chain
- chain 统一编排跨模块动作

### 3.3 数据访问目录不是 `repositories/`，而是 `db/*_oper.py`

MoviePilot 当前 `app/db/` 直接放操作对象，例如：

- `downloadhistory_oper.py`
- `subscribe_oper.py`
- `systemconfig_oper.py`
- `transferhistory_oper.py`

而 ORM 模型在：

- `app/db/models/*.py`

这说明它的持久化分层语义是：

- `db/models` 表达数据模型
- `db/*_oper.py` 表达数据库访问操作
- 不存在单独 `repositories/` 概念

### 3.4 支撑层不是 `adapters/`，而是 `helper/` 与 `modules/`

MoviePilot 当前：

- `helper/` 放本地辅助逻辑，例如目录、格式化、下载器辅助、规则、订阅、RSS、通知等
- `modules/` 放外部系统能力和宿主模块能力，例如下载器、媒体服务器、TMDB/TVDB、消息渠道等

这说明它并不使用一个笼统的 `adapters/` 来承接所有对接逻辑，而是明确区分：

- 本地支撑
- 外部能力

### 3.5 启动装配不是 `tasks/`，而是 `startup/`

MoviePilot 有单独的 `startup/`，而不是把启动装配和调度入口长期放在 `tasks/` 目录里。

这意味着 MusicPilot 若要对齐：

- 启动装配
- 宿主调度注册
- 本地 loop
- 生命周期收口

都应向 `startup/` 收敛，而不是继续留在 `tasks/` 或散落在 `__init__.py`、`main.py` 中。

## 4. MoviePilot 的主流程代码风格

### 4.1 endpoint 薄，chain 厚

以 MoviePilot 当前实现为例：

- `app/api/endpoints/search.py` 直接引入 `MediaChain`、`SearchChain`
- `app/api/endpoints/download.py` 直接引入 `DownloadChain`、`MediaChain`

endpoint 的职责主要是：

- 参数边界
- 鉴权
- 调用 chain
- 返回响应

不会把跨模块主流程留在 endpoint 自己内部。

### 4.2 ChainBase 是统一基类

MoviePilot 的 `app/chain/__init__.py` 提供 `ChainBase`，统一承接：

- cache
- event manager
- plugin/module manager
- 消息能力
- 共通错误处理

这说明：

- chain 不是一组随意命名的类
- 而是一套有统一基座的主流程编排体系

### 4.3 主流程编排写在 chain 里，不写在支撑层里

以 `app/chain/transfer.py` 为例，`TransferChain` 内部包含：

- 任务扫描
- 作业管理
- 状态推进
- 失败回写
- 调用其他链和支撑对象

这说明 MoviePilot 的主流程原则是：

- 支撑对象做局部能力
- chain 负责编排全流程

这也是 MusicPilot 当前最需要对齐的一点。

## 5. MusicPilot 对齐后的目标结构

MusicPilot 后端在同构重构完成后，长期目标结构应为：

```text
backend/app/
  api/
    endpoints/
  chain/
  core/
  db/
    models/
    *_oper.py
  helper/
  modules/
  schemas/
  startup/
  utils/
```

说明：

- 这里是“等价职责同构”的目标结构
- `plugins/`、`workflow/`、`agent/` 不提前创建空壳目录
- 但如果 MusicPilot 后续出现对应职责，目录命名也必须沿 MoviePilot 方式扩展

## 6. MusicPilot 需要落地的 9 条主链

为了与 MoviePilot 的主流程模式对齐，MusicPilot 当前阶段至少要完成这 9 条链：

| MusicPilot 主链 | 对齐的 MoviePilot 主链语义 | 说明 |
|---|---|---|
| `MusicMediaChain` | `MediaChain` | 统一音乐媒体解析链 |
| `MusicMediaServerChain` | `MediaServerChain` | 媒体库同步与媒体服务器侧后处理 |
| `MusicSearchChain` | `SearchChain` | query preview、search job、candidate 决策 |
| `MusicDownloadChain` | `DownloadChain` | dispatch、binding/task 状态推进 |
| `MusicTransferChain` | `TransferChain` | 下载后整理闭环、handoff、preview/apply |
| `MusicSubscribeChain` | `SubscribeChain` | 订阅 CRUD、run、scheduler |
| `MusicChartChain` | MoviePilot discover/list + refresh 模式 | 榜单、discovery、refresh、entry -> subscribe |
| `MusicDashboardChain` | `DashboardChain` | summary 与运行态聚合 |
| `MusicSystemChain` | `SystemChain` 风格入口 | settings / probe / health / root 运行态入口 |

## 7. MusicPilot 当前目录到目标结构的映射

### 7.1 API 层

当前：

- `backend/app/api/routes/`

目标：

- `backend/app/api/endpoints/`

并按业务语义重排为：

- `media.py`
- `search.py`
- `download.py`
- `transfer.py`
- `subscribe.py`
- `chart.py`
- `dashboard.py`
- `settings.py`
- `probe.py`

### 7.2 主流程层

当前：

- `backend/app/services/`

目标：

- `backend/app/chain/`

规则：

- 不保留 `Service` 命名
- 不保留 `services/` 目录
- 不允许 route/scheduler 继续直接调旧主流程文件

### 7.3 数据层

当前：

- `backend/app/models/`
- `backend/app/repositories/`

目标：

- `backend/app/db/models/`
- `backend/app/db/*_oper.py`

规则：

- 不保留 `Repository` 命名
- 不保留 `repositories/` 目录

### 7.4 支撑层

当前：

- `backend/app/adapters/`

目标：

- `backend/app/helper/`
- `backend/app/modules/`

规则：

- 本地支撑、纯解析、纯算法、路径/布局/组织辅助进入 `helper/`
- 外部系统、宿主、provider、下载器、storage 对接进入 `modules/`
- 不保留 `Adapter` 命名与 `adapters/` 目录

### 7.5 运行装配层

当前：

- `backend/app/tasks/`
- 部分散落在 `backend/app/__init__.py`
- 部分散落在 `backend/app/main.py`

目标：

- `backend/app/startup/`

规则：

- 调度注册、本地 loop、生命周期收口统一放入 `startup/`
- 不保留 `Task` 目录作为长期主结构

## 8. 不允许留下的伪对齐结果

以下结果都不算“对齐 MoviePilot”：

1. 有 `chain/`，但 route 还是直接调旧支撑对象
2. 有 `Music*Chain`，但 chain 只是 `return old_object.method()`
3. `services/`、`repositories/`、`adapters/`、`tasks/` 还保留在活跃代码里
4. `plugin_runtime` 还保持旧结构，只在主仓做新结构
5. 只改类名，不改目录和文件命名
6. 只改主流程，不改测试组织和启动装配方式

## 9. MusicPilot 允许保留的唯一差异

与 MoviePilot 同构，不等于复用影视模型。

MusicPilot 允许保留的差异只有两类：

1. 领域语义差异
   - 影视 `MetaInfo / MediaInfo`
   - 对应为音乐 `MusicMediaInput / MusicMetaBase / MusicMediaInfo`

2. 当前尚无等价职责的目录不提前建空壳
   - 如 `agent/`、`workflow/`
   - 只有当 MusicPilot 出现对应职责时，再按 MoviePilot 命名补齐

除此之外，不应再保留“因为项目历史原因所以先继续用旧目录”的例外。

## 10. 对当前重构 spec 的补充约束

为了避免最后重构不彻底，后续实现必须额外满足：

1. 后端活跃结构不再保留 `Service`、`Repository`、`Adapter`、`Task` 概念
2. 旧目录必须物理删除，而不是退出主路径
3. `core/dependencies.py` 不能重新装配旧主流程对象
4. 测试组织应优先围绕 `chain`、`api/endpoints`、`db/*_oper.py`
5. `plugin_runtime/plugins/musicpilot/` 后端镜像必须同构
6. README、backend README、架构文档不能继续用旧目录概念描述后端主结构

## 11. 最终判断标准

只有同时满足下面这些条件，才能说 MusicPilot 后端“完全对齐 MoviePilot”：

1. 目录结构同构
2. 文件命名同构
3. 主流程入口同构
4. 持久化分层同构
5. 支撑层分工同构
6. 启动装配方式同构
7. `plugin_runtime` 镜像同构
8. 只保留音乐领域语义差异，不再保留历史结构差异
