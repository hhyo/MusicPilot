# MusicPilot

MusicPilot 是一个参考 MoviePilot 插件体系思路构建的音乐能力扩展工程。本仓库当前只完成 Phase 0（T01-T04），目标是先交付可启动、可构建、可装配、可继续迭代的工程骨架，而不是提前实现真实榜单、搜索、订阅、下载、整理业务。

## 项目简介

- `frontend/`：基于 Vue 3 + TypeScript + Vite 的独立前端壳，当前提供 App Shell、首页工作台占位和基础路由。
- `backend/`：基于 FastAPI 的后端脚手架，当前提供最小可运行服务、健康检查、统一响应结构和后续分层预留目录。
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
- API 骨架可继续扩展

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
- 五个一级目录初始化
- 前端 Vue 3 + TS + Vite 工程骨架
- 后端 FastAPI 工程骨架
- plugin_runtime 占位产物结构
- scripts 与版本同步脚本

## 当前阶段未完成范围

- 真实榜单拉取
- 真实 Artist / Album / Track 搜索
- 真实订阅 CRUD
- 真实 PT 搜索、匹配、下载派发
- 真实整理、标签、媒体库刷新
- 真实 MoviePilot 宿主安装与挂载逻辑

以上能力本轮均只保留目录、接口、注释或说明性占位，不提前实现。

## 下一阶段建议推进方式

1. 基于现有 FastAPI 骨架补齐 Phase 1 的探针 API 与统一 DTO。
2. 明确宿主适配接口，再向 `adapters/` 中补具体探针和 mock。
3. 以搜索页和契约路由为第一条联调主线，避免同时扩展所有业务面。
4. 保持 `plugin_runtime/` 只作为构建产物边界，不把开发源码和宿主产物混放。

