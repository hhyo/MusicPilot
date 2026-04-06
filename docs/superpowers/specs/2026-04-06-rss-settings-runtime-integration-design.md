# RSS Settings Runtime Integration Design

Date: 2026-04-06

## Context

MusicPilot 当前已经完成了 RSS discovery provider 的第一轮实现：

- 正式 provider 为 `rss_feed`
- 当前支持 5 个 family：
  - `netease_playlist_tracks`
  - `netease_artist_songs`
  - `netease_artist_albums`
  - `youtube_top_songs`
  - `youtube_top_artists`
- RSS 条目已经能通过 `search_lookup` 进入现有 metadata drawer

但当前 RSS discovery 仍停留在“结构层”和“环境变量层”：

- 后端 `Settings` 已有 `chart_rss_feeds` 字段，但仍主要依赖环境变量注入
- `/settings/providers` 仍是 placeholder
- 前端 `/settings` 仍是占位页

这意味着 RSS discovery 虽然已经具备正式 provider 结构，却还没有正式进入项目自己的 settings 体系。

用户当前希望推进的是：

1. RSS feed 的 settings 配置接入
2. 真实运行态验证
3. 把网易云 / YouTube feed 真正跑进 discovery

同时用户已经明确的边界是：

- 这轮先走 settings
- 这轮不做可视化 RSS feed 管理页
- 这轮不继续停留在结构层
- 这轮不扩新的 RSS family

## Goals

1. 让 RSS discovery feed 配置正式进入 MusicPilot 项目设置，而不是只依赖环境变量。
2. 让 `/settings/providers` 从 placeholder 变为真实可读写接口。
3. 让前端 `/settings` 从 placeholder 变为最小可用的配置入口。
4. 让 RSS discovery 运行时优先读取项目设置，并保留环境变量作为 fallback。
5. 在真实运行态里验证：通过 settings 保存的网易云 / YouTube feed 能进入 discovery。

## Non-Goals

这一轮不做：

- RSS feed 的复杂可视化 CRUD 管理页
- family 手工配置
- feed 表格排序、批量导入、字段级校验 UI
- 新的 RSS family 扩展
- discovery 页面结构重做
- metadata provider 扩展
- 下载、dispatch、organize 主链改造

## Product Direction

这一轮的产品方向不是“做完整设置中心”，而是：

- 把 RSS discovery 配置从环境变量提升为项目内正式设置
- 提供一个最小但真实可用的设置入口
- 让用户可以在系统内查看、编辑并保存当前 RSS discovery feeds

也就是说，这一轮的设置页目标是“正式接入”，不是“完整产品化配置管理”。

## Recommended Approach

推荐方案是：

1. 新增项目内设置存储
2. 将 `/settings/providers` 改为真实接口
3. 用一个最小 settings 页面承接读取和保存
4. 运行时优先读取项目设置，环境变量作为 fallback

推荐理由：

- 能直接满足“settings 正式接入”
- 不需要一口气做复杂 UI
- 不破坏现有 RSS provider 主结构
- 后续若要做可视化 feed 管理页，可以直接在这一轮的 settings 模型之上继续增强

## Storage Design

### New Persistence Unit

新增一张极薄的项目内设置表：

- `app_settings`

建议字段：

- `key`：字符串主键
- `value_json`：JSON 存储
- `updated_at`：更新时间

第一轮只存以下键：

- `chart_provider_mode`
- `chart_rss_feeds`

### Why a Dedicated Settings Table

不复用当前其他业务表的原因：

- RSS feeds 属于项目级配置，不是订阅、metadata 或 organize 运行记录
- 独立的 key-value / JSON 结构最利于最小实现和后续扩展
- 后续如果还要把更多 settings 纳入项目内持久化，可以沿用同一张表

### Value Shape

`chart_rss_feeds` 的值仍沿用当前已经确定的结构：

```json
[
  {
    "id": "netease-hot-tracks",
    "label": "网易云热歌榜",
    "url": "https://rsshub.rssforever.com/163/music/playlist/3778678",
    "category": "hot",
    "region": "CN",
    "enabled": true
  }
]
```

系统继续自动识别：

- `family`
- `chart_type`
- `resolution_mode`

这些字段不进入设置存储。

## Backend API Design

### Existing Route Reuse

继续沿用当前已有 settings 路由：

- `GET /settings/providers`
- `PUT /settings/providers`

但语义从 placeholder 升级为真实接口。

### Response Shape

第一轮不追求“大而全 provider 设置总览”，只返回当前真正会被前端编辑的最小结构：

- `chart_provider_mode`
- `chart_rss_feeds`
- metadata provider 当前模式可只读回显

即：

```json
{
  "chart_provider_mode": "rss_feed",
  "chart_rss_feeds": [...],
  "metadata_provider_mode": "musicbrainz"
}
```

### Update Semantics

`PUT /settings/providers` 允许更新：

- `chart_provider_mode`
- `chart_rss_feeds`

第一轮不允许通过这个接口修改：

- metadata provider 复杂参数
- host integration 大量运行参数

这样可以把这轮的范围稳定收在 RSS discovery settings。

## Runtime Resolution Rules

### Priority Order

RSS discovery 运行时读取配置的优先级：

1. 项目内 settings
2. 环境变量 fallback

具体规则：

- 如果 `app_settings.chart_rss_feeds` 存在且非空，优先使用它
- 否则 fallback 到当前 `Settings.chart_rss_feeds`

`chart_provider_mode` 同理：

1. 项目内设置优先
2. 环境变量 fallback

### Why This Order

这样做的原因是：

- 一旦 settings 页保存成功，用户应立即看到系统行为变化
- 但不应破坏当前本地开发、宿主运行时和测试里已经存在的环境变量启动方式

## Frontend Design

### Route Scope

前端继续使用现有 `/settings` 路由，不新增新页面层级。

当前 `ModulePlaceholderView` 替换为真实最小设置页。

### First-Round UI Scope

第一轮 settings 页面只包含：

1. `Chart Provider Mode`
   - 下拉选择
   - 至少支持：
     - `mock`
     - `listenbrainz`
     - `rss_feed`

2. `RSS Feed 配置`
   - 结构化 JSON 文本区
   - 展示当前 feed 配置
   - 支持编辑与保存

3. `保存`
   - 明确成功 / 失败反馈

4. `当前说明`
   - 告知：
     - family 自动识别
     - 当前支持的 family 范围
     - 保存后会影响榜单页 discovery

### Explicitly Deferred UI

这一轮明确不做：

- 表格化 feed CRUD
- 新增 / 编辑 / 删除单条表单
- 自动 URL 校验交互
- family 手工选择
- 拖拽排序
- 独立“测试 feed”按钮

## Validation Rules

### Minimum Test Coverage

至少覆盖：

1. `app_settings` 的存取
2. `/settings/providers` 真实读写
3. 运行时优先读取项目设置，环境变量为 fallback
4. 前端 `/settings` 页面加载、保存和基本错误展示
