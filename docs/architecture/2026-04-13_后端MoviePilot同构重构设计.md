# 后端 MoviePilot 同构重构设计

> 用途：定义 MusicPilot 后端如何在目录结构、命名方式、主流程编排方式和代码风格上与 MoviePilot 完整对齐。本文只覆盖后端与 `plugin_runtime` 后端镜像，不覆盖前端。

## 1. 设计目标

本轮重构目标不是“继续在现有 `services/` 架构上补 Chain”，而是把 MusicPilot 后端直接重构为与 MoviePilot 同构的形态：

- 主业务流程统一由 `Music*Chain` 编排
- API endpoint、调度入口、插件宿主注册直接调用 `Music*Chain`
- 后端目录结构、文件命名和组织方式与 MoviePilot 对齐
- 旧的 `api/routes`、`services`、`models`、`repositories`、`adapters` 不再作为长期主结构保留
- 不为旧结构保留兼容层，不做双轨目录，不做中间转发层

本轮保留的唯一差异是业务语义：

- MoviePilot 使用影视语义
- MusicPilot 保留音乐语义

因此，对齐的是设计方法、目录和代码风格，而不是复用 MoviePilot 的影视模型。

## 2. 非目标

本轮不处理：

- 前端重构
- 新增 metadata provider
- 新增榜单源
- 新增宿主接口
- 改写宿主内部实现

本轮也不做：

- 兼容性 wrapper
- 旧目录对新目录的转发 import
- 新旧 route 双轨并行
- `Service` 包装 `Chain` 的过渡实现

## 3. 目标结构

重构完成后，后端长期结构固定为：

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
```

对应约束：

- `backend/app/api/routes/` 退出活跃主路径
- `backend/app/services/` 退出活跃主路径
- `backend/app/models/` 迁入 `backend/app/db/models/`
- `backend/app/repositories/` 迁入 `backend/app/db/*_oper.py`
- `backend/app/adapters/` 按职责迁入 `helper/` 或 `modules/`
- 后端活跃结构不再保留 `Service` 概念

### 3.1 `api/endpoints`

文件命名对齐 MoviePilot 的领域文件名：

- `media.py`
- `search.py`
- `download.py`
- `transfer.py`
- `subscribe.py`
- `chart.py`
- `dashboard.py`
- `settings.py`
- `probe.py`

说明：

- `jobs.py` 语义收进 `search.py`
- `downloads.py` 收进 `download.py`
- `subscriptions.py` 收进 `subscribe.py`
- `charts.py` 收进 `chart.py`
- `organize.py` 主语义收进 `transfer.py`

### 3.2 `chain`

后端主流程只保留这 7 条链：

- `MusicMediaChain`
- `MusicSearchChain`
- `MusicDownloadChain`
- `MusicTransferChain`
- `MusicSubscribeChain`
- `MusicChartChain`
- `MusicDashboardChain`

文件名按 MoviePilot 风格对齐：

- `chain/media.py`
- `chain/search.py`
- `chain/download.py`
- `chain/transfer.py`
- `chain/subscribe.py`
- `chain/chart.py`
- `chain/dashboard.py`

类命名保留 MusicPilot 语义，统一使用 `Music*Chain`。

### 3.3 `db`

数据库层统一采用 MoviePilot 风格：

- ORM 模型进入 `db/models/`
- 数据访问对象采用 `*_oper.py`

初始映射目标：

- `acquisition_oper.py`
- `orchestration_oper.py`
- `charts_oper.py`
- `settings_oper.py`
- `metadata_oper.py`

### 3.4 `helper`

放纯工具与本地支撑逻辑，例如：

- 格式化
- 解析辅助
- 路径与布局辅助
- organize 策略辅助
- 纯算法型辅助

### 3.5 `modules`

放外部系统、宿主、provider 对接逻辑，例如：

- metadata provider
- chart provider
- host http / downloader / storage runtime
- host probe / host search

## 4. 主入口规则

重构完成后，以下入口只能直接调用 `Music*Chain`：

- API endpoint
- 宿主 `get_service()` 注册入口
- 本地 backend loop

禁止的组织方式：

- endpoint 直接编排多个旧支撑对象
- scheduler 直接编排多个旧支撑对象
- 以任何 `Service` 概念承担完整跨模块主流程
- 为保留旧结构，在新链外再加一层 facade

## 5. 7 条主链职责

## 5.1 `MusicMediaChain`

职责：

- 统一音乐媒体解析链唯一主入口
- 输入归一
- `MusicMediaInput -> MusicMetaBase -> MusicMediaInfo`
- detail hydrate

支撑逻辑保留：

- 输入适配
- meta 构建
- 识别
- hydrator

`/media/*` 以及 detail 相关入口全部直接调用该链。

## 5.2 `MusicSearchChain`

职责：

- query preview
- search job create / run / retry / cancel / delete
- candidate confirm / reject
- 搜索状态推进与回写

它吸收现有 `query_builder`、`search_job`、`scoring` 的主编排逻辑。

## 5.3 `MusicDownloadChain`

职责：

- dispatch
- binding / task 状态推进
- retry dispatch
- 下载工作台聚合

它吸收现有 `dispatch` 与 `downloads_workspace` 的主编排逻辑。

## 5.4 `MusicTransferChain`

职责：

- 下载后整理主链
- handoff 解析
- organize preview / apply
- repair / retry / rebuild preview
- 下载闭环状态回写

它吸收现有：

- pending handoff
- host path handoff
- organize 自动闭环编排
- downloads workspace 中与 handoff/repair 相关的主流程

这是 MusicPilot 对齐 MoviePilot `TransferChain` 的核心。

## 5.5 `MusicSubscribeChain`

职责：

- subscription create / update / archive
- run / preview_only / retry_run
- run list / detail
- scheduler 执行入口

它吸收现有 `subscriptions`、`subscription_execution`、`subscription_scheduler` 的主编排逻辑。

## 5.6 `MusicChartChain`

职责：

- chart provider list
- chart list / detail / runtime
- refresh / refresh_all
- discovery entry 组装
- chart entry -> subscription

它吸收现有 `charts` 与 `discovery` 的主编排逻辑。

## 5.7 `MusicDashboardChain`

职责：

- dashboard summary
- 运行态聚合
- diagnostics 摘要

它吸收现有 `dashboard` 的主编排逻辑。

## 6. 同步与异步边界

重构后统一采用以下规则：

- endpoint 层不承担主流程编排，只负责参数和响应边界
- `Music*Chain` 对外暴露少量顶层业务方法
- 链内部再拆私有步骤方法
- 同步 / 异步边界以 endpoint 和底层外部调用为界，不再在 route 内临时混用

## 7. `MusicChainBase`

新增 `backend/app/chain/__init__.py`，提供 `MusicChainBase`。

职责只限于：

- 链名与统一日志入口
- 共通缓存辅助
- 宿主 / 插件运行态辅助
- 统一错误包装与诊断输出辅助

`MusicChainBase` 不承载业务流程本身，不做万能工具箱。

## 8. 旧结构的处理原则

本轮按激进重构处理，旧结构的规则如下：

- `api/routes`：删除，不保留转发
- `services`：删除，不保留任何活跃代码
- `models`：删除
- `repositories`：删除
- `adapters`：删除

如果某个旧文件中的逻辑仍然有效：

- 主流程逻辑搬入 `chain`
- 数据访问逻辑搬入 `db/*_oper.py`
- 纯工具搬入 `helper`
- 外部系统对接搬入 `modules`

不保留：

- alias import
- deprecated wrapper
- 兼容性 facade

## 9. `plugin_runtime` 同步规则

`plugin_runtime/plugins/musicpilot/` 必须与 `backend/app/` 保持同构：

- 同样采用 `api/endpoints`
- 同样采用 `chain`
- 同样采用 `db/models` 与 `db/*_oper.py`
- 同样取消旧目录语义

后端主仓完成结构重排后，`plugin_runtime` 必须同步调整，不允许继续维持“主仓新结构 + runtime 旧结构”。

## 10. 验收标准

完成条件不是“功能还能跑”，而是同时满足：

1. 活跃代码中不再存在：
   - `backend/app/api/routes/`
   - `backend/app/services/`
   - `backend/app/models/`
   - `backend/app/repositories/`
   - `backend/app/adapters/`
2. API endpoint 只直接调用 `Music*Chain`
3. 宿主 `get_service()` 只注册 `Music*Chain`
4. 本地 loop 只调用 `Music*Chain`
5. `plugin_runtime` 后端镜像与主仓结构同构
6. backend 全量测试通过
7. `python3 scripts/package_plugin.py` 通过
8. README / backend README / 架构文档同步到新结构

## 11. 实施边界

本设计只定义这轮后端激进同构重构的边界，不定义实现顺序细节。  
实现阶段应围绕本文，不再回退到旧目录保留、旧命名兼容或 service 编排延续。
