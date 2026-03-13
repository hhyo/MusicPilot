# Chart Module 设计

## 📋 模块概述

Chart Module 负责聚合和展示各大音乐榜单数据，提供榜单追踪和新歌提醒功能。

## 🎯 功能需求

1. **榜单聚合**: 集成多个榜单数据源
2. **数据缓存**: 本地缓存减少 API 调用
3. **榜单追踪**: 用户可关注感兴趣榜单
4. **趋势显示**: 显示歌曲排名变化

## 🏗️ 数据模型

### Chart
```python
class Chart:
    id: str              # 唯一标识 (e.g., "billboard-hot-100")
    source: str          # 数据源 (billboard, qqmusic)
    name: str            # 榜单名称
    region: str          # 地区
    last_updated: datetime
    update_frequency: int  # 更新频率(小时)
```

### ChartTrack
```python
class ChartTrack:
    id: int
    chart_id: str
    rank: int
    track_id: int        # 关联本地曲库
    title: str
    artist: str
    cover_url: str
    previous_rank: int   # 上期排名 (null=新上榜)
    weeks_on_chart: int  # 在榜周数
```

## 🔌 数据源集成

### Billboard
- API: Billboard API (需申请)
- Fallback: 网页爬取
- 更新频率: 每周

### QQ音乐
- API: QQ音乐 API
- 更新频率: 每日

### 苹果音乐
- API: Apple Music API
- 更新频率: 每日

## 💾 缓存策略

- Redis 缓存榜单数据
- 缓存过期时间: 1-24小时 (根据榜单更新频率)
- 本地 SQLite 备份

## 🔔 提醒功能

- 新歌进入榜单 Top 10
- 歌曲排名大幅上升/下降
- 用户关注的榜单更新