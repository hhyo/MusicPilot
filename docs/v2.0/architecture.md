# MusicPilot v2.0 架构设计

## 🏗️ 整体架构

v2.0 在 v1 架构基础上进行扩展，保持三层架构：
- **Frontend**: Vue 3 + TypeScript
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL + Redis

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Vue 3)                        │
├─────────────────────────────────────────────────────────────┤
│  v1 功能        │    Chart    │   Organize   │  MediaServer │
│  现有页面       │   Module    │    Module    │    Module    │
└────────┬────────┴──────┬──────┴───────┬───────┴──────┬───────┘
         │               │              │              │
         └───────────────┴──────────────┴──────────────┘
                          │
                    ┌─────▼─────┐
                    │  FastAPI  │
                    │  Backend  │
                    └─────┬─────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
    ┌────▼────┐     ┌─────▼─────┐    ┌─────▼─────┐
    │PostgreSQL│     │   Redis   │    │ FileSystem│
    └─────────┘     └───────────┘    └───────────┘
```

## 📦 新增模块

### Chart Module

```
Chart Module
├── api/              # 榜单 API 集成
│   ├── billboard.py  # Billboard 数据
│   ├── qqmusic.py    # QQ音乐数据
│   └── cache.py      # 数据缓存
├── models/           # 数据模型
│   ├── chart.py      # 榜单模型
│   └── trend.py      # 趋势模型
└── services/
    └── scheduler.py  # 定时任务服务
```

### Organize Module

```
Organize Module
├── rules/            # 整理规则
│   ├── base.py       # 基础规则
│   ├── move.py       # 移动规则
│   └── rename.py     # 重命名规则
├── processor/        # 处理器
│   ├── metadata.py   # 元数据处理
│   ├── cover.py      # 封面处理
│   └── lyrics.py     # 歌词处理
└── detector/         # 检测器
    └── duplicate.py  # 重复检测
```

### MediaServer Module

```
MediaServer Module
├── server/           # DLNA/UPnP 服务
│   ├── core.py       # 核心服务
│   ├── device.py     # 设备发现
│   └── renderer.py   # 渲染控制
├── chromecast/       # Chromecast
│   ├── client.py     # 客户端
│   └── controller.py # 控制器
└── transcoder/       # 转码器
    └── ffmpeg.py     # FFmpeg 封装
```

## 🔌 API 扩展

### Chart API
- `GET /api/v2/charts` - 获取榜单列表
- `GET /api/v2/charts/{id}` - 获取特定榜单
- `GET /api/v2/charts/{id}/tracks` - 获取榜单曲目

### Organize API
- `POST /api/v2/organize/rules` - 创建整理规则
- `POST /api/v2/organize/execute` - 执行整理
- `GET /api/v2/organize/duplicate` - 检测重复

### MediaServer API
- `GET /api/v2/mediaserver/devices` - 获取可用设备
- `POST /api/v2/mediaserver/cast` - 投放到设备
- `POST /api/v2/mediaserver/transcode` - 转码请求

## 🗄️ 数据库扩展

### 新增表

```sql
-- Chart Module
CREATE TABLE charts (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50),      -- billboard, qqmusic
    chart_id VARCHAR(100),
    name VARCHAR(255),
    last_updated TIMESTAMP
);

CREATE TABLE chart_tracks (
    id SERIAL PRIMARY KEY,
    chart_id INTEGER REFERENCES charts(id),
    rank INTEGER,
    track_id INTEGER REFERENCES tracks(id),
    previous_rank INTEGER
);

-- Organize Module
CREATE TABLE organize_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    rule_type VARCHAR(50),   -- move, rename, classify
    config JSONB,
    enabled BOOLEAN DEFAULT true
);

-- MediaServer Module
CREATE TABLE cast_sessions (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(100),
    device_name VARCHAR(255),
    status VARCHAR(20),
    started_at TIMESTAMP
);
```

## 🔄 向后兼容

- v1 所有 API 保持不变（/api/v1/*）
- v2 新增 API 使用 /api/v2/* 前缀
- 数据库迁移使用 Alembic
- 前端路由添加 /v2/ 前缀