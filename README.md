# MusicPilot

MusicPilot 是一个参考 MoviePilot 插件体系思路构建的音乐能力扩展工程。当前仓库已完成 Phase 0、Phase 1、Phase 2、Phase 3 与 Phase 4，重点先交付可启动、可构建、可装配、可联调的工程骨架，以及从 metadata 到 QueryBuilder、SearchJob、候选评分、mock dispatch，再到 subscriptions、mock chart discovery、subscription run、mock organize preview 的最小闭环，而不是提前实现生产级自动化。

## 项目简介

- `frontend/`：基于 Vue 3 + TypeScript + Vite 的独立前端壳，当前提供首页工作台、metadata 搜索页、榜单页、订阅页，以及从 metadata / chart item 创建订阅、执行一次 run、查看 organize preview 的最小前端闭环。
- `backend/`：基于 FastAPI 的后端工程，当前提供统一响应结构、宿主探针骨架、metadata 搜索 API、SQLite 最小落库、QueryBuilder、SearchJob、评分、mock dispatch、SubscriptionService、mock chart discovery 与 mock organize boundary。
- `plugin_runtime/`：面向未来 MoviePilot 宿主集成的运行时占位产物目录，当前只保留 manifest、静态资源、后端挂载说明和打包边界。
- `scripts/`：前端开发、后端开发、前端构建、插件装配、版本同步脚本。
- `docs/`：产品方案、架构方案、规范与任务拆解文档，按要求保持原位不变。

## 仓库结构

```text
MusicPilot/
  frontend/
  backend/
  docs/
  scripts/
  plugin_runtime/
  README.md
  .gitignore
  .editorconfig
  .env.example
```

## 本地开发启动方式

前端：

```bash
cd frontend
pnpm install
pnpm dev
```

也可以直接运行：

```bash
./scripts/dev_frontend.sh
```

后端：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.db_init --reseed
uvicorn app.main:app --reload
```

也可以直接运行：

```bash
./scripts/dev_backend.sh
```

## 前后端构建方式

前端构建：

```bash
./scripts/build_frontend.sh
```

后端当前为源码运行形态，不提供 wheel 或容器产物，只保证：

- `uvicorn app.main:app --reload` 可启动
- `GET /health` 返回 200
- metadata search / detail API 可访问
- QueryBuilder / SearchJob / candidate / dispatch mock API 可访问
- subscriptions / charts / organize preview API 可访问

## 数据初始化与 seed

Phase 4 继续采用最小可运行方案：`SQLite + SQLAlchemy + local seed metadata + mock acquisition / chart / organize data`。

- 默认数据库文件：`backend/data/musicpilot.db`
- 手动初始化或重置 seed：

```bash
cd backend
python -m app.db_init --reseed
```

- 正常启动后端时也会自动建表，并在库为空时导入本地 seed
- 当前 seed 只用于验证 Artist / Album / Track 搜索链路、mock chart entry 和 subscription run 输入，不代表已经真实接入第三方音乐源或真实榜单源

## 当前执行模式与 mock 边界

- Subscription 执行模式：当前仅支持手动触发一次同步 run，不启用生产级 cron、消息队列或分布式 scheduler。
- Chart discovery：当前为 local seed / mock chart source，只验证发现入口与从 chart item 创建订阅的动作。
- Host search：当前仍通过 mock host search adapter 返回稳定候选，用于打通 run -> candidate summary。
- Dispatch：当前仍是 mock dispatch boundary，不会真实创建下载任务。
- Organize：当前仅生成 organize preview 与状态记录，不会真实执行文件移动、硬链接、标签写入或媒体库刷新。

## plugin_runtime 打包说明

Phase 0 的 `plugin_runtime/` 仍是占位运行时目录，不伪造真实 MoviePilot 宿主安装逻辑。当前提供的打包链路负责：

1. 将 `frontend/dist/` 装配到 `plugin_runtime/plugins/musicpilot/static/`
2. 将 `backend/app/` 装配到 `plugin_runtime/plugins/musicpilot/`
3. 将 `backend/requirements.txt` 同步到 `plugin_runtime/plugins/musicpilot/requirements.txt`
4. 保留 `manifest/` 与边界说明文件，供后续真实接入宿主时继续收敛

执行命令：

```bash
./scripts/package_plugin.sh
```

## 当前阶段完成范围

- Phase 0 / T01-T04
- Phase 1 / T05-T07
- Phase 2 / T08-T10
- Phase 3 / T11-T14
- Phase 4 / 订阅与编排最小闭环
- 宿主能力探针 API 骨架
- MVP 路由骨架与统一响应结构
- metadata 搜索服务最小可用版
- SQLite 最小落库与本地 seed
- 前端搜索页最小闭环与详情视图
- QueryBuilder、SearchJob、候选评分与 mock dispatch 最小闭环
- 订阅模型与 API、mock charts/discovery、subscription run 记录与 mock organize preview

## 当前阶段未完成范围

- 真实榜单拉取与增量监控
- 真实第三方 metadata provider 接入
- 生产级订阅调度器与重试编排
- 真实 PT 搜索、匹配、下载派发
- 真实整理、标签、媒体库刷新
- 真实 MoviePilot 宿主安装与挂载逻辑

以上能力本轮均只保留目录、接口、注释或说明性占位，不提前实现。

## 下一阶段建议推进方式

1. 在保留现有 response envelope 的前提下，引入真实 metadata provider adapter。
2. 将 mock chart source、mock host search、mock dispatch、mock organize 分别替换为真实 adapter。
3. 在当前 SubscriptionExecutionService 骨架上补完整调度、重试、下载完成回调与 organize job 状态机。
4. 保持 `plugin_runtime/` 只作为构建产物边界，不把开发源码和宿主产物混放。
