# MusicPilot Project Rules

> 用途：记录 MusicPilot 项目的长期工程边界、文档组织约束与执行规则。本文不记录临时阶段实现细节。

## Product Priorities

- 先保证主链真实可用，再做扩展能力。
- settings 可先落地，前端可视化配置可后补。

## Project Invariants

- 一级目录保持为：
  - `frontend/`
  - `backend/`
  - `docs/`
  - `scripts/`
  - `plugin_runtime/`
- 不随意新增无关一级目录。
- 技术栈固定为：
  - `frontend`: Vue 3 + TypeScript + Vite
  - `backend`: FastAPI
  - `plugin_runtime`: 面向后续打包集成的插件运行时目录
- 包管理、脚本和工程组织优先沿用仓库现有方式，不随意引入偏离当前结构的新体系。

## Documentation Rules

- 新文档的组织规则：
  - 产品方案优先放 `docs/product/`
  - 技术与架构方案优先放 `docs/architecture/`
  - 规范、契约、清单、任务拆解文件优先放 `docs/` 根目录
- 已存在于 `docs/` 的历史文件保持原位，不随意移动。
- 不允许删除 `docs/` 中已有文件。
- 每个阶段能力收口后，同步更新：
  - `README.md`
  - `backend/README.md`
  - 当前路线或运行态验证文档
- 文档必须反映真实当前状态，不保留已过期的阶段性表述。

## Engineering Principles

- 优先保证工程结构清晰、命名明确、边界稳定。
- 优先做最小可运行实现，再逐步增强，不做脱离当前阶段目标的过度设计。
- settings 可先落地，可视化管理后补，但语义和扩展面要提前定稳。
- 新能力优先选择最简单、最利于后续扩展的一种组织方式。

## Architecture Rules

- MusicPilot 维护自己的音乐业务语义，不把 MoviePilot 的影视业务语义直接当成默认主语义。
- 后端业务主流程严格参考 MoviePilot 的 `Chain` 组织方式与代码风格实现。凡是跨步骤、跨模块、需要编排状态推进的主链路，应优先实现为明确的 `Music*Chain`。
- `Chain` 是后端主流程的唯一推荐组织方式：
  - 输入归一
  - 主流程编排
  - 状态推进
  - 结果回写
  都应在 `Chain` 内统一收口。
- 后端目录结构与命名方式应优先向 MoviePilot 对齐，目标形态固定为：
  - `backend/app/api/endpoints/`
  - `backend/app/chain/`
  - `backend/app/core/`
  - `backend/app/db/`
  - `backend/app/db/models/`
  - `backend/app/db/*_oper.py`
  - `backend/app/helper/`
  - `backend/app/modules/`
  - `backend/app/schemas/`
  - `backend/app/startup/`
  - `backend/app/utils/`
- 与 MoviePilot 有等价职责的目录、文件名和分层方式必须保持一致；如当前项目暂时没有对应职责，可不创建空壳目录，但不允许继续用旧目录承担该职责。
- `api/routes`、`services`、`models`、`repositories`、`adapters`、`tasks` 不作为长期主结构保留；后端活跃结构不再保留 `Service`、`Repository`、`Adapter`、`Task` 概念与对应目录。
- 文件命名优先对齐 MoviePilot 的领域文件名，例如 `media.py`、`search.py`、`download.py`、`transfer.py`、`subscribe.py`、`chart.py`、`dashboard.py`；类命名保留音乐领域语义，统一使用 `Music*Chain`。
- API endpoint、宿主 `get_service()` 调度注册、本地 loop 入口都只能直接调用 `Music*Chain`。
- 支撑逻辑统一落到：
  - `db/*_oper.py`
  - `helper/`
  - `modules/`
  - `core/`
  - `startup/`
  - `utils/`
  不再通过 `Service`、`Repository`、`Adapter`、`Task` 命名或旧目录承载。
- 启动装配、调度注册、生命周期管理统一进入 `startup/`；无领域含义的通用工具统一进入 `utils/`；`core/dependencies.py` 不得重新引入旧主流程对象或旧目录概念。
- 测试组织也要与目标结构同步，优先围绕 `chain`、`api/endpoints`、`db/*_oper.py` 组织，不再以旧 `service/repository/adapter` 视角划分主测试单元。
- `plugin_runtime/plugins/musicpilot/` 后端镜像必须与主仓后端保持同构，不允许出现“主仓新结构 + runtime 旧结构”的长期例外。
- 统一音乐媒体解析链是上层业务的基础语义；涉及发现、详情、搜索、订阅、获取、库内线索等输入时，优先收敛到 `MusicMediaInput -> MusicMetaBase -> MusicMediaInfo`，而不是在各模块各自维护零散 hints 或来源特判。
- 优先复用宿主底层能力与明确接口语义，不把宿主现有业务语义直接硬套到音乐场景。
- 每个场景优先对应一个清晰主调用语义，不引入 recommendation / strategy / matrix 驱动的运行时业务 fallback。
- 新能力接入时优先保持扩展点统一，不按单一来源或单一模块临时拼接主结构。
- 跨模块链路应通过稳定桥接层连接，不在页面或零散调用点里堆来源特判。
- 当前后端主链长期目标固定为：
  - `MusicMediaChain`
  - `MusicMediaServerChain`
  - `MusicSearchChain`
  - `MusicDownloadChain`
  - `MusicTransferChain`
  - `MusicSubscribeChain`
  - `MusicChartChain`
  - `MusicDashboardChain`
  - `MusicSystemChain`

## Delivery Rules

- 不跳过当前阶段提前实现未经确认的后续阶段能力。
- 如果设计文档中某些能力尚无完整细节，优先补：
  - 占位接口
  - 占位结构
  - 说明性 TODO 注释
  不擅自扩展复杂业务逻辑。
- 不伪造不存在的 MoviePilot 宿主真实接口实现；允许保留 adapter / interface / mock / placeholder。
- 所有实现优先保证：
  - 能启动
  - 能构建
  - 能打包
  - 便于下一阶段继续开发
- scripts 至少要覆盖并保持清晰：
  - 前端开发环境启动
  - 后端开发环境启动
  - 前端构建
  - `plugin_runtime` 打包
  - 版本同步或版本占位脚本
- README 至少要长期覆盖：
  - 项目简介
  - 仓库结构说明
  - 本地开发启动方式
  - 前后端构建方式
  - `plugin_runtime` 打包说明
  - 当前阶段完成范围
  - 当前阶段未完成范围
  - 下一阶段建议推进方式

## Implementation Style

- 代码风格保持简洁、一致。
- 占位文件和目录命名必须清晰，不使用随意临时命名。
- 能运行的地方尽量跑通，不能跑通的地方要给出明确 TODO 注释或文档说明。
- 不生成大段空文件；占位文件也应包含最小可理解内容。
- 不为了“看起来完整”而生成大量无意义模板代码。
- 如需进行后端主结构重排，优先采用激进替换而不是兼容性双轨；不为了保留旧目录、旧命名或旧主流程入口而做折中结构。
- 后端主结构重排完成时，旧目录应物理删除，不保留 wrapper、alias import、deprecated facade 或转发壳文件。
- 若出现多种工程组织方案，优先选择最简单、最利于后续扩展的一种。
- 若文档中存在解释空间，优先遵守：
  - 非侵入式插件扩展
  - 宿主适配边界清晰
  - 可打包

## Verification Discipline

- 任何涉及外部集成、核心业务主链或关键用户交互的改动，优先做真实运行态验证。
- 不把环境问题包装成代码完成。
- 不把占位、mock 或本地替身结果表述成真实环境成功。
- 完成后优先执行最小必要验证，不省略验证步骤。
- 关键前端交互完成后，尽量保留真实截图证据。
