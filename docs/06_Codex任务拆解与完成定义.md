# 06. Codex 任务拆解与完成定义

## 6.1 使用方式
本文件是给 Codex 的直接任务清单。每个任务都包含：
- 输入
- 输出
- 依赖
- 完成定义（DoD）

## 6.2 Phase 0：仓库与插件壳

### T01 初始化仓库骨架
**目标**：创建 `musicpilot/frontend backend docs scripts plugin_runtime`  
**输出**：
- 根目录 README / .gitignore / .env.example
- 五个一级目录
**DoD**：
- 目录全部存在
- README 能说明如何启动前后端
- plugin_runtime 有标准插件占位目录

### T02 初始化前端脚手架
**目标**：创建 Vue 3 + TS + Vite 工程  
**输出**：
- `frontend/package.json`
- `src/main.ts`
- `src/App.vue`
- `src/router/index.ts`
**DoD**：
- `pnpm install && pnpm dev` 可启动
- 首页显示 MusicPilot 占位页面

### T03 初始化后端脚手架
**目标**：创建 FastAPI 工程  
**输出**：
- `backend/pyproject.toml`
- `app/main.py`
- `app/api/health.py`
**DoD**：
- `uvicorn app.main:app --reload` 可启动
- `GET /health` 返回 200

### T04 初始化插件运行时模板
**目标**：创建 MoviePilot 插件标准产物模板  
**输出**：
- `plugin_runtime/package.json`
- `plugin_runtime/plugins/musicpilot/__init__.py`
- `plugin_runtime/plugins/musicpilot/requirements.txt`
**DoD**：
- 构建脚本可以将前后端产物装配到 plugin_runtime

## 6.3 Phase 1：宿主探针与基础契约

### T05 实现探针 API
**目标**：实现 health / sites / search / downloaders / dispatch / notify / config 探针  
**依赖**：T03、T04  
**DoD**：
- 所有探针 API 可调用
- 有日志与 request_id
- 能输出验证样例

### T06 完成宿主能力验证记录
**目标**：按《宿主能力探针验证清单》执行并记录  
**DoD**：
- P03/P05/P08/P11 至少通过
- docs 中留下验证记录

### T07 落地 API 契约骨架
**目标**：按照 OpenAPI 建立 FastAPI 路由与 schema 占位  
**输出**：
- dashboard/charts/search/subscriptions/jobs/downloads/organize/settings 路由文件
- Pydantic DTO
**DoD**：
- 所有 MVP 路由返回 mock 数据
- OpenAPI 文档可自动生成

## 6.4 Phase 2：元信息与搜索

### T08 实现 MetadataService
**目标**：建立 Artist/Album/Track 搜索与详情服务  
**DoD**：
- 搜索页可返回实体列表
- 详情页可读取实体详情

### T09 落地数据库模型与 Alembic 迁移
**目标**：把 SQL 结构映射为 ORM 与迁移  
**DoD**：
- 可以一键迁移
- 关键表创建成功
- 有最小 seed 数据

### T10 实现搜索页前后端联调
**目标**：搜索页可按 artist/album/track 工作  
**DoD**：
- 输入关键词得到分页结果
- 可进入详情页
- 空态/错误态完整

## 6.5 Phase 3：PT 获取与下载

### T11 实现 QueryBuilder
**目标**：基于 Album/Track/Artist 构造 PT 查询词  
**DoD**：
- 支持标准词、别名词、宽松词
- 有单元测试覆盖

### T12 实现 SearchJob 与候选结果流程
**目标**：从“搜索资源”动作创建 SearchJob 并拿到候选列表  
**DoD**：
- 创建 job
- 调用宿主 PT 搜索
- 结果可持久化到 `music_search_result`

### T13 实现音乐评分引擎
**目标**：按艺人、专辑、年份、音质、版本打分  
**DoD**：
- 结果包含 `score_total` 与 `score_breakdown`
- 可以产出 auto/manual/reject 决策

### T14 实现下载确认与派发
**目标**：下载页可展示候选并派发到宿主下载器  
**DoD**：
- 人工确认弹窗可用
- 自动下载阈值可配置
- 派发后生成 `music_download_binding`

## 6.6 Phase 4：订阅与整理

### T15 实现 SubscriptionService
**目标**：支持 chart/artist/album/track 四类订阅  
**DoD**：
- 可 CRUD
- 可立即执行
- 有状态流转

### T16 实现榜单订阅与艺人订阅扫描
**目标**：自动发现命中并触发 SearchJob  
**DoD**：
- 榜单刷新产生命中
- 艺人订阅扫描产生命中

### T17 实现 OrganizerService
**目标**：下载完成后进行标签写入、目录归档、媒体库刷新  
**DoD**：
- 生成 organize job
- 支持失败重试
- 整理日志可查询

## 6.7 Phase 5：稳定化

### T18 前后端契约校验
**DoD**：
- 状态枚举统一
- 错误码统一
- 前端不直接依赖数据库字段名

### T19 测试补齐
**DoD**：
- QueryBuilder / Scorer / OrganizerRules 单测覆盖
- 核心 API 集成测试可跑
- 至少 1 条端到端主链路通过

### T20 打包与发布脚本
**DoD**：
- 一条命令生成 `plugin_runtime` 标准产物
- 版本号自动同步
- zip 包可交付

## 6.8 完成定义（项目级）
MVP 完成必须同时满足：
1. 有独立 MusicPilot 入口
2. 搜索页可搜索 Artist/Album/Track
3. 可从详情页发起“搜索资源”
4. 能生成 SearchJob 和候选结果
5. 能人工确认或自动触发下载
6. 下载完成后能进入整理流程
7. 订阅页可管理四类订阅
8. 打包脚本可生成标准插件产物
