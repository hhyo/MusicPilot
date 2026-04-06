# RSS Discovery Provider Design

Date: 2026-04-06

## Context

MusicPilot 已经有一套可工作的 discovery 主结构：

- 真实 discovery provider 已经支持 `ListenBrainz`
- discovery productization 已完成
- chart detail 已能通过 `DiscoveryTarget` 下钻到 metadata detail drawer
- chart 响应已经经过统一的 discovery assembly
- metadata/detail 与 discovery UI 已经形成稳定交互壳

当前的新目标不是再扩一个单独站点 provider，而是把一类正式的 RSS 发现源纳入现有 discovery 体系。

这轮用户明确给出的 RSS 来源集中在两类：

1. RSSHub 网易云音乐相关路线
2. RSSHub YouTube charts 路线

同时用户希望：

- RSS discovery 是正式榜单/发现源，不是临时导入脚本
- feed 通过配置输入
- 系统按照 RSS 类型自动处理并生成榜单列表
- discovery 到 metadata 的转化层要提前定义好，避免后续榜单扩充时大量重构

用户同时确认：

- 第一轮不做豆瓣
- 第一轮不做前端可视化 RSS 配置页
- 第一轮 discovery -> metadata 使用 `search_lookup`

## Goals

1. 增加一个正式的 `rss_feed` discovery provider。
2. 通过结构化 settings 配置若干 RSS feed 源。
3. 自动识别当前支持的 RSS feed family，并生成统一 chart 列表。
4. 让 RSS chart entry 能进入现有 discovery 页面与 metadata detail drawer。
5. 所有 RSS chart entry 第一轮统一通过 `search_lookup` 转化到 metadata。
6. 让后续继续扩更多 RSS feed family 时，不需要重构 discovery 主结构。

## Non-Goals

这一轮不做：

- 豆瓣 latest feeds
- YouTube `TopVideos`
- 前端可视化 RSS feed 管理页
- 任意 RSS 自动推断引擎
- RSS feed snapshot 持久化与 diff 跟踪
- discovery -> search 自动转化
- download / dispatch / organize 主链改造
- 新 metadata provider 扩展

## Product Direction

RSS discovery 在产品上应该是“正式发现源”，而不是“调试入口”。

这意味着：

- RSS feeds 会像其他 discovery provider 一样出现在榜单页
- 不同 RSS family 的条目仍然统一进入现有 discovery 页面
- 用户看到的是 chart / entry / metadata detail 的一致体验
- provider-specific 的 URL、RSS XML 结构、字段提取方式不进入前端页面逻辑

第一轮产品方向不是“做一个万能 RSS 阅读器”，而是“把已知的音乐 RSS discovery family 纳入正式发现入口”。

## Supported Scope

### First-Round Provider

正式 provider 名称：

- `rss_feed`

### First-Round Supported Families

第一轮一次性支持以下 family：

- `netease_playlist_tracks`
- `netease_artist_songs`
- `netease_artist_albums`
- `youtube_top_songs`
- `youtube_top_artists`

### Entity-Type Mapping

family 到 `chart_type` 的映射固定如下：

- `netease_playlist_tracks` -> `track`
- `netease_artist_songs` -> `track`
- `netease_artist_albums` -> `album`
- `youtube_top_songs` -> `track`
- `youtube_top_artists` -> `artist`

### Explicitly Deferred

- `youtube_top_videos`
- `douban_latest_albums`
- 其他 RSSHub 音乐路线
- 非 RSSHub 的任意 RSS 自动适配

## Design Overview

### Current Discovery Chain

当前 discovery 链路大致是：

`ChartProviderAdapter -> DiscoveryAssembler -> ChartService -> /charts API -> ChartsView`

这个主链保持不变。

### New Discovery Chain

这一轮新增 RSS 之后，链路变成：

`RssFeedChartProviderAdapter -> RssFeedFamilyParser -> DiscoveryAssembler -> ChartService -> /charts API -> ChartsView`

关键点：

- `RssFeedChartProviderAdapter` 负责 feed 拉取、XML 解析、family 识别和标准 chart/item 生成
- `RssFeedFamilyParser` 负责 family-specific 的字段提取
- `DiscoveryAssembler` 继续负责产品化 discovery 视图与 `DiscoveryTarget`

### Why This Structure

这套结构能保证：

- provider 不按“网易云/YouTube”拆碎
- family-specific 逻辑不泄漏到 service/UI
- 后续扩更多 RSS feed family 时，只增加 parser，不重做 discovery 主结构

## Configuration Model

### Config Ownership

第一轮 RSS feed 配置放在 settings 体系中，不做前端可视化管理页。

这是一个正式产品配置，不是临时本地文件。

### Feed Entry Shape

每条 RSS feed 配置至少包含：

- `id`
- `label`
- `url`
- `category`
- `region`
- `enabled`

### Example Shape

```json
[
  {
    "id": "netease-hot-tracks",
    "label": "网易云热歌榜",
    "url": "https://rsshub.rssforever.com/163/music/playlist/3778678",
    "category": "hot",
    "region": "CN",
    "enabled": true
  },
  {
    "id": "youtube-top-songs-global",
    "label": "YouTube 热门歌曲榜",
    "url": "https://rsshub.rssforever.com/youtube/charts/TopSongs",
    "category": "hot",
    "region": "Global",
    "enabled": true
  }
]
```

### What Is Not Configured Manually

以下字段不要求手填：

- `family`
- `chart_type`
- `resolution_mode`

这些都由系统根据 URL 与内容结构自动推断。

## Family Detection

### Detection Strategy

第一轮按 URL 做强约束识别，不做内容层模糊猜测。

### Rules

- URL 包含 `/163/music/playlist/`
  - `family = netease_playlist_tracks`
- URL 包含 `/163/music/artist/songs/`
  - `family = netease_artist_songs`
- URL 包含 `/163/music/artist/`
  - `family = netease_artist_albums`
- URL 包含 `/youtube/charts/TopSongs`
  - `family = youtube_top_songs`
- URL 包含 `/youtube/charts/TopArtists`
  - `family = youtube_top_artists`

### Unsupported URLs

未命中以上规则的 feed：

- 第一轮直接标记为 unsupported
- 不做自动 fallback family guessing
- 不允许其拖垮整个 provider

## Chart Construction

### One Feed => One Chart

每条 feed 配置在运行时生成一个 chart。

### Chart Fields

chart 的关键字段规则：

- `chart.id`
  - `rss-feed-{feed.id}`
- `chart.chart_source`
  - `rss_feed`
- `chart.chart_name`
  - 优先配置里的 `label`
  - fallback 到 `channel.title`
- `chart.chart_type`
  - 由 family 决定
- `chart.region`
  - 优先配置里的 `region`
- `chart.category`
  - 直接用配置里的 `category`
- `chart.note`
  - 标明当前来自 RSS discovery source
- `integration_point`
  - `RssFeedChartProviderAdapter`

## Feed Item Extraction

### Shared Output Shape

不管 family 差异多大，family parser 最终都应提取出统一的中间结构：

- `target_name`
- `subtitle`
- `provider_origin_url`
- `provider_origin_id`
- `cover_url`
- `published_at`
- `family`
- `raw_context`

### Family-Specific Extraction

#### 1. `netease_playlist_tracks`

来源特征：

- channel 是歌单
- item link 指向 `song?id=...`
- description 可提取歌手、专辑、发行日期、封面

提取字段：

- `target_name`
  - 歌曲标题
- `subtitle`
  - 歌手
- `provider_origin_id`
  - song id
- `provider_origin_url`
  - item link
- `cover_url`
  - description 中的 img
- `published_at`
  - RSS item `pubDate`
- `raw_context`
  - 专辑、发行日期等

#### 2. `netease_artist_songs`

来源特征：

- channel 是歌手歌曲
- item link 指向 `song?id=...`
- description 可提取歌手、专辑、封面

提取字段与 playlist tracks 基本一致，但 chart 语义是“艺人新歌”。

#### 3. `netease_artist_albums`

来源特征：

- channel 是歌手专辑
- item link 指向 `album?id=...`
- description 可提取歌手、专辑、发行日期、封面

提取字段：

- `target_name`
  - 专辑名
- `subtitle`
  - 歌手
- `provider_origin_id`
  - album id
- `provider_origin_url`
  - item link
- `cover_url`
  - description 中的 img
- `published_at`
  - RSS item `pubDate`
- `raw_context`
  - 专辑名、发行日期

#### 4. `youtube_top_songs`

来源特征：

- item link 指向 YouTube watch url
- `title` 是歌曲标题
- `author` 是歌手
- description 主要是嵌入播放器

提取字段：

- `target_name`
  - 歌曲标题
- `subtitle`
  - 歌手
- `provider_origin_id`
  - YouTube video id
- `provider_origin_url`
  - item link
- `cover_url`
  - 可以从 video id 推导或暂时为空
- `published_at`
  - RSS item `pubDate`
- `raw_context`
  - 原始标题、原始 author

#### 5. `youtube_top_artists`

来源特征：

- item link 指向 `charts.youtube.com/artist/...`
- `title` 是 artist name
- description 相对弱

提取字段：

- `target_name`
  - 艺人名
- `subtitle`
  - 可为空
- `provider_origin_id`
  - charts artist path 中的稳定标识
- `provider_origin_url`
  - item link
- `cover_url`
  - 暂时为空
- `published_at`
  - RSS item `pubDate`
- `raw_context`
  - 原始 URL / title

## DiscoveryTarget Strategy

### Resolution Mode

这一轮 RSS discovery 所有条目统一使用：

- `resolution_mode = search_lookup`

不会要求 RSS 条目自带 MusicBrainz id。

### Why Not direct_id

原因很直接：

- 网易云 RSS 条目主要提供 song/album 链接和文本元数据
- YouTube charts 条目主要提供 title/artist/video link
- 这些数据足够做 lookup，但不足以稳定直接打开 metadata detail id

所以第一轮应该先定义并统一 `search_lookup`，而不是强行伪造 direct-id 流程。

## discovery -> metadata Lookup Hints

### Shared Principle

RSS 条目进入 metadata drawer 时，不再依赖 provider 原始 payload。

它们只通过 `DiscoveryTarget` 携带最小 lookup hints。

### Hints by Family

#### `netease_playlist_tracks`

- `title`
- `artist_name`
- `album_title`
- `provider_origin_url`
- `provider_origin_id`
- `published_at`

#### `netease_artist_songs`

- `title`
- `artist_name`
- `album_title`
- `provider_origin_url`
- `provider_origin_id`

#### `netease_artist_albums`

- `album_title`
- `artist_name`
- `published_at`
- `provider_origin_url`
- `provider_origin_id`

#### `youtube_top_songs`

- `title`
- `artist_name`
- `provider_origin_url`
- `provider_origin_id`

#### `youtube_top_artists`

- `artist_name`
- `provider_origin_url`
- `provider_origin_id`

## Frontend Responsibilities

### Charts Page

这轮不新增 RSS 专用页面。

RSS charts 继续进入现有：

- chart list
- chart detail
- grouped entry view
- metadata detail drawer

### Interaction

用户交互保持一致：

- 浏览 chart
- 点击条目
- 打开 metadata detail drawer

区别只在内部：

- RSS 条目统一通过 `search_lookup` 解析，而不是 `direct_id`

### UI Scope

前端这一轮只需要：

- 正常渲染 RSS charts
- 在 entry 上保持一致的 discovery badges
- 显示 conversion state / note
- 不做 feed 管理页

## Error Handling

### Feed Fetch Failure

单个 feed 拉取失败时：

- 只影响该 chart
- 不影响整个 `rss_feed` provider 的其他 feed

### Unsupported Family

未识别 family 的 feed：

- 标记 unsupported
- 不进入正常 chart 列表
- 日志和 note 中保留原因

### Weak Lookup Context

某些 YouTube/网易云条目可能只有弱 hints。

第一轮处理原则：

- 仍可进入 `search_lookup`
- `conversion_note` 明确标识为 lookup-based target
- 不伪装成 direct-id ready

## Testing Strategy

第一轮至少需要覆盖：

1. settings 中 RSS feeds 配置解析
2. family URL 识别
3. 5 个 family 的 item extraction
4. chart list/detail 构造
5. RSS entries 的 `DiscoveryTarget` 全部走 `search_lookup`
6. 前端 charts 视图能渲染 RSS charts
7. RSS entries 能沿现有 metadata drawer 流程进入 lookup path

## Recommendation

第一轮按“正式 `rss_feed` provider + family adapters”实现，是当前最稳的路径。

这样做的收益是：

- 能一次性覆盖你已经给出的网易云与 YouTube RSS 发现入口
- 不会因为后面再加更多 RSS routes 就推翻结构
- 可以把 RSS discovery 直接纳入现有 productized discovery 页面
- 同时把 `search_lookup` 转化层真正用于正式 provider，而不是只停留在概念上
