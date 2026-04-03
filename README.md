# MusicPilot

MusicPilot 是一个参考 MoviePilot 插件体系思路构建的音乐能力扩展工程。当前仓库已完成 Phase 0、Phase 1 与 Phase 2，重点先交付可启动、可构建、可装配、可联调的工程骨架与 metadata 搜索最小闭环，而不是提前实现真实 PT 搜索、下载派发、订阅执行与整理规则。

## 项目简介

- `frontend/`：基于 Vue 3 + TypeScript + Vite 的独立前端壳，当前提供 App Shell、首页工作台、metadata 搜索页和详情抽屉最小闭环。
- `backend/`：基于 FastAPI 的后端工程，当前提供统一响应结构、宿主探针骨架、metadata 搜索 API、SQLite 最小落库与本地 seed。
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

后端当前为源码运行形态，Phase 0 不提供 wheel 或容器产物，只保证：

- `uvicorn app.main:app --reload` 可启动
- `GET /health` 返回 200
- metadata search / detail API 可访问

## 数据初始化与 seed

Phase 2 采用最小可运行方案：`SQLite + SQLAlchemy + local seed metadata`。

- 默认数据库文件：`backend/data/musicpilot.db`
- 手动初始化或重置 seed：

```bash
cd backend
python -m app.db_init --reseed
```

- 正常启动后端时也会自动建表，并在库为空时导入本地 seed
- 当前 seed 只用于验证 Artist / Album / Track 搜索链路，不代表已经真实接入第三方音乐源

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
- 宿主能力探针 API 骨架
- MVP 路由骨架与统一响应结构
- metadata 搜索服务最小可用版
- SQLite 最小落库与本地 seed
- 前端搜索页最小闭环与详情视图

## 当前阶段未完成范围

- 真实榜单拉取
- 真实第三方 metadata provider 接入
- 真实订阅 CRUD / 调度
- 真实 PT 搜索、匹配、下载派发
- 真实整理、标签、媒体库刷新
- 真实 MoviePilot 宿主安装与挂载逻辑

以上能力本轮均只保留目录、接口、注释或说明性占位，不提前实现。

## 下一阶段建议推进方式

1. 在保留现有 response envelope 的前提下，引入真实 metadata provider adapter。
2. 基于当前结构化 metadata 字段补 QueryBuilder，作为后续 PT 查询输入。
3. 为订阅、下载、整理继续沿用非侵入式 adapter/service 边界。
4. 保持 `plugin_runtime/` 只作为构建产物边界，不把开发源码和宿主产物混放。
