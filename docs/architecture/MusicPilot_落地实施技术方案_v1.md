# MusicPilot 落地实施技术方案

> 基于独立插件入口 + MoviePilot 宿主能力复用 + 音乐域补强  
> 文档定位：面向研发实施的技术蓝图  
> 输入依据：现有顶层设计文档 + UI&UX 产品方案 + 页面原型截图

## 1. 文档目标与实施边界

### 1.1 实施目标
- 在不侵入 MoviePilot 原影视业务代码与主页面逻辑的前提下，交付一个独立的 MusicPilot 插件入口。
- 形成从音乐发现、实体检索、订阅、PT 获取、下载、整理到入库的完整闭环。
- 在工程层面落成可实施的前后端模块、服务接口、任务编排与构建发布方案。
- 让 UI/UX 文档中的页面、模块、字段与交互能够与技术实现一一映射。

### 1.2 范围定义
| 层级 | 纳入本方案 | 不纳入 V1 | 备注 |
|---|---|---|---|
| 产品能力 | 榜单、搜索、订阅、PT 获取、下载、整理、设置 | 推荐算法、社交热度、播放器 | 聚焦业务闭环 |
| 接入边界 | 插件独立入口、独立 API、独立数据域 | 修改原影视页面与原订阅模型 | 保持非侵入 |
| PT 侧能力 | 复用宿主站点配置、基础搜索、下载器派发 | 重复实现通用 PT 搜索底座 | 音乐只做查询与匹配补强 |
| 工程交付 | 源码工程 + 标准插件产物 | 运行时动态改目录 | 构建期产出标准插件目录 |

## 2. 产品与技术闭环概述

### 2.1 闭环总览
发现 → 实体确认 → 订阅/获取触发 → PT 搜索与匹配 → 下载派发 → 整理入库

### 2.2 页面—能力—技术模块映射
| 页面/入口 | 用户目标 | 核心后端能力 | 关键数据对象 |
|---|---|---|---|
| 首页 | 查看工作台状态与快捷入口 | dashboard aggregation / unread task summary | TaskSummary, SubscriptionSummary |
| 榜单页 | 发现与批量订阅 | chart provider / chart subscription service | Chart, ChartEntry, ChartSubscription |
| 搜索页 | 检索艺人/歌曲/专辑 | metadata search service / search aggregation | Artist, Album, Track |
| 订阅页 | 管理四类订阅对象 | subscription service / policy engine | Subscription, RuleProfile |
| 下载页 | 查看 PT 命中并确认下载 | acquisition orchestrator / dispatcher | SearchJob, SearchResult, DownloadBinding |
| 整理页 | 跟踪入库、异常与重试 | organizer service / library sync | LibraryItem, OrganizeJob, OrganizeLog |

## 3. 系统总体架构

### 3.1 分层架构
- 宿主平台层：登录/权限、插件装载、下载器、站点管理、通知、调度。
- 插件运行时层：插件注册、配置管理、远程前端挂载、API 命名空间。
- MusicPilot 业务层：榜单、搜索、订阅、PT 获取、整理、任务状态。
- 外部集成层：音乐元数据源、榜单源、PT 站点、下载器、媒体库。

### 3.2 逻辑组件图
```text
┌───────────────────────────────────────────────────────────────────┐
│                     MoviePilot Host / Plugin Runtime             │
│ auth │ permission │ scheduler │ notifier │ downloader │ sites    │
└───────────────┬───────────────────────────────────────────────────┘
                │
      ┌─────────▼──────────────────────────────────────────┐
      │                  MusicPilot Plugin                │
      │ frontend shell │ api gateway │ services │ tasks   │
      │ charts │ metadata │ acquisition │ organizer        │
      └───────┬───────────────┬───────────────┬───────────┘
              │               │               │
        榜单源/元数据源      PT站点搜索       下载器/媒体库
```

## 4. 前端架构与页面实施方案

### 4.1 前端模块分层
| 层 | 模块 | 职责 | 产物 |
|---|---|---|---|
| 入口层 | app shell / route registry | 宿主入口挂载、路由注册、布局壳 | remote entry |
| 页面层 | dashboard/charts/search/subscriptions/downloads/organize/settings | 页面编排、数据请求、状态组合 | page components |
| 领域组件层 | entity card/filter bar/result list/subscription form/task drawer | 通用音乐组件与交互复用 | reusable UI blocks |
| 基础层 | api client/store/type guards/utils/theme | 请求封装、状态管理、类型与主题 | shared libs |

### 4.2 页面实施清单
| 页面 | 核心模块 | 主交互 | 依赖 API | 状态重点 |
|---|---|---|---|---|
| 首页 | 搜索框、快捷入口、统计卡、最近任务 | 跳转/下钻/恢复历史 | /dashboard/summary, /tasks/recent | 加载/空/失败/部分可用 |
| 榜单页 | 平台切换、榜单卡片、筛选抽屉、批量订阅栏 | 筛选、查看详情、批量订阅 | /charts/providers, /charts, /charts/{id}, /subscriptions | 缓存回显、批量选择、订阅成功 |
| 搜索页 | 关键词输入、实体 tabs、结果列表、筛选器 | 搜索、分页、快速订阅、进入详情 | /search, /artists/{id}, /albums/{id}, /tracks/{id} | 防抖、空结果、切页、类型切换 |
| 订阅页 | 四类订阅列表、编辑抽屉、启停开关 | 编辑规则、立即执行、暂停/恢复 | /subscriptions, /subscriptions/{id}/run | 并发刷新、操作反馈 |
| 下载页 | 候选结果列表、确认弹窗、下载绑定卡 | 自动/手动下载、重试、忽略 | /jobs, /jobs/{id}/results, /downloads/dispatch | 候选评分、确认态、下载中 |
| 整理页 | 日志列表、异常项、规则预览 | 重试、忽略、查看差异 | /organize/jobs, /library/items | 可追溯、异常聚合 |

## 5. 后端架构与服务分层

### 5.1 服务分层
| 层 | 服务/模块 | 职责 | 是否独立实现 |
|---|---|---|---|
| API 层 | musicpilot.api.* | 参数校验、鉴权、DTO 映射、响应包装 | 独立 |
| 应用层 | chart_app, search_app, subscription_app, acquisition_app, organize_app | 编排用例、事务边界、触发任务 | 独立 |
| 领域层 | entity / policy / matcher / scorer / organizer rules | 业务规则、评分、策略与状态机 | 独立 |
| 基础设施层 | site adapters, downloader gateway, metadata adapters, repo, cache | 复用宿主适配能力并补充音乐适配 | 部分复用 |

### 5.2 核心服务
- ChartService：榜单列表、详情、快照、订阅事件。
- MetadataService：Artist/Album/Track 搜索与详情。
- SubscriptionService：四类订阅生命周期与命中事件。
- AcquisitionService：PT 搜索、评分与自动下载决策。
- OrganizerService：音乐标签写入、目录归档、媒体库刷新。
- TaskService：作业调度、重试与恢复。

## 6. PT 获取链路：复用与独立实现边界

### 6.1 复用宿主能力
- PT 站点配置、登录态、可用性检测、站点启停与优先级。
- 多站点并行搜索底座、基础 parser/spider、站点层限流与失败降级。
- 下载器列表、默认下载器选择、任务派发、状态回调与通知。

### 6.2 独立实现能力
- 音乐查询构建器。
- 音乐匹配评分与过滤扩展。
- 自动下载决策。
- 音乐整理规则。

### 6.3 查询构建示例
```text
Album:  周杰伦 太阳之子 2026 FLAC
Album:  Jay Chou Children Of The Sun 2026 FLAC
Track:  周杰伦 太阳之子 single FLAC
Track:  Jay Chou Children Of The Sun track FLAC
Filter: -live -concert -cover -karaoke
```

## 7. 数据模型与存储设计

### 7.1 核心实体模型
| 实体 | 主键建议 | 关键字段 | 关系 | 用途 |
|---|---|---|---|---|
| Artist | mbid/platform_id/hash | name, aliases, country, active_years | 1:N Album / Track | 元信息基础 |
| Album | upc/mbid/platform_id/hash | title, aliases, year, release_type, audio_profile_pref | N:1 Artist; 1:N Track | 专辑级订阅与整理 |
| Track | isrc/mbid/platform_id/hash | title, aliases, track_no, version, duration | N:1 Album; N:M Artist | 歌曲级搜索与命中 |
| Chart | provider+chart_id | name, category, region, refresh_cron | 1:N ChartEntry | 发现入口 |
| Subscription | uuid | media_type,target_type,target_id,rule_json,status | 1:N Hit / Job | 统一订阅 |

### 7.2 作业与结果模型
- music_search_job
- music_search_result
- music_match_record
- music_download_binding
- music_organize_job

## 8. API 设计

### 8.1 API 分组
- Dashboard
- Charts
- Metadata Search
- Subscriptions
- Acquisition
- Organize
- Settings

### 8.2 关键接口示例
```json
POST /api/v1/plugin/musicpilot/search
{
  "keyword": "周杰伦",
  "type": "album",
  "filters": {"year": 2026, "release_type": ["album","ep"]},
  "page": 1,
  "page_size": 20
}
```

```json
POST /api/v1/plugin/musicpilot/jobs
{
  "target_type": "album",
  "target_id": "alb_xxx",
  "trigger_source": "manual",
  "profile_id": "default-lossless"
}
```

```json
POST /api/v1/plugin/musicpilot/downloads/dispatch
{
  "result_id": "res_xxx",
  "downloader_id": "default",
  "save_path_policy": "auto",
  "manual_confirm": true
}
```

## 9. 关键交互时序图

### 9.1 手动搜索并下载
```text
User -> Frontend SearchPage: 输入关键词 + 选择 Album
Frontend -> Search API: POST /search
Search API -> MetadataService: searchAlbum(keyword, filters)
MetadataService -> Frontend: album results
User -> Frontend: 进入 AlbumDetail 并点击「搜索资源」
Frontend -> Acquisition API: POST /jobs
Acquisition API -> QueryBuilder: build queries
Acquisition API -> Host PT Search: multi-site search
Host PT Search -> Acquisition API: raw results
Acquisition API -> Matcher/Scorer: score candidates
Acquisition API -> Frontend: ranked results
User -> Frontend: 点击下载
Frontend -> Dispatch API: POST /downloads/dispatch
Dispatch API -> Host Downloader: create task
Host Downloader -> OrganizerService: completion callback
OrganizerService -> Library: organize + refresh
```

### 9.2 榜单订阅自动下载
```text
Scheduler -> ChartService: refresh charts
ChartService -> ChartSnapshot: save current snapshot
ChartService -> SubscriptionService: emit chart delta hits
SubscriptionService -> AcquisitionService: create SearchJob for Track/Album
AcquisitionService -> Host PT Search: search by metadata queries
AcquisitionService -> Scorer: compute score & decision
Decision(auto) -> Downloader: dispatch
Decision(manual) -> DownloadsPage: pending confirmation
```

## 10. 状态机与任务编排

### 10.1 SearchJob 状态机
```text
queued -> running -> matched -> dispatched -> completed
                      └-> manual_pending -> dispatched
                      └-> no_result
queued/running -> failed -> retrying -> running
```

### 10.2 整理作业状态机
```text
queued -> running -> tag_written -> moved -> refreshed -> completed
running -> failed -> retrying -> running
failed -> ignored
```

## 11. 工程目录与构建发布

### 11.1 源码工程目录
```text
musicpilot/
  frontend/
  backend/
  docs/
  scripts/
  plugin_runtime/
```

### 11.2 发布目录映射
```text
source repo                           release artifact
musicpilot/frontend/build   ───────▶ plugin_runtime/static/
musicpilot/backend/*        ───────▶ plugin_runtime/plugins/musicpilot/
musicpilot/scripts/package  ───────▶ package.json + requirements.txt
```

## 12. 可观测性、安全与非功能要求
- request/job/binding/organize 全链路都要有可追踪 ID。
- 不记录站点敏感凭据与密钥。
- PT 多站点搜索异步化，不阻塞基础实体搜索。
- 结果页与任务页需要面向失败、空结果、人工确认做完整状态设计。

## 13. 测试策略与实施计划

### 13.1 测试矩阵
- 单元测试：QueryBuilder / Scorer / OrganizerRules。
- 集成测试：metadata adapters / PT adapters / downloader gateway。
- 前后端联调：搜索、订阅、下载确认、整理日志。
- 端到端：榜单订阅自动下载、手动搜索下载、整理回调。

### 13.2 实施阶段建议
- Phase 0：骨架搭建与插件运行打通。
- Phase 1：元数据搜索与详情闭环。
- Phase 2：PT 获取与下载闭环。
- Phase 3：整理入库与自动化。
- Phase 4：榜单与自动订阅。
- Phase 5：稳定化与发布。

### 13.3 风险与缓解
- PT 命中不稳定：建立 score_breakdown 与人工确认兜底。
- 元数据字段不统一：建立标准化映射层与 alias cache。
- 插件目录不一致：构建期生成标准插件产物。
- 前后端状态不一致：定义统一状态枚举与契约测试。
