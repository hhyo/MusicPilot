# MusicPilot v2.0 API 设计

## 📋 API 版本

- **v1**: 现有 API，保持不变
- **v2**: 新增功能 API

## Chart Module API

### 获取榜单列表
```
GET /api/v2/charts

Response:
{
  "charts": [
    {
      "id": "billboard-hot-100",
      "source": "billboard",
      "name": "Hot 100",
      "region": "US",
      "last_updated": "2026-03-13T00:00:00Z"
    }
  ]
}
```

### 获取榜单详情
```
GET /api/v2/charts/{chart_id}

Response:
{
  "id": "billboard-hot-100",
  "source": "billboard",
  "name": "Hot 100",
  "tracks": [
    {
      "rank": 1,
      "title": "Song Title",
      "artist": "Artist Name",
      "cover_url": "https://...",
      "previous_rank": 2
    }
  ]
}
```

### 获取追踪的榜单
```
GET /api/v2/charts/following

Response:
{
  "charts": [...]
}
```

### 关注榜单
```
POST /api/v2/charts/{chart_id}/follow

Response:
{
  "success": true
}
```

## Organize Module API

### 获取整理规则列表
```
GET /api/v2/organize/rules

Response:
{
  "rules": [
    {
      "id": 1,
      "name": "按艺术家分类",
      "rule_type": "move",
      "config": {
        "pattern": "{artist}/{album}/{title}"
      },
      "enabled": true
    }
  ]
}
```

### 创建整理规则
```
POST /api/v2/organize/rules
{
  "name": "按艺术家分类",
  "rule_type": "move",
  "config": {
    "pattern": "{artist}/{album}/{title}"
  }
}

Response:
{
  "id": 1,
  "success": true
}
```

### 执行整理任务
```
POST /api/v2/organize/execute
{
  "rule_id": 1,
  "dry_run": false
}

Response:
{
  "task_id": "task-123",
  "status": "started"
}
```

### 检测重复文件
```
POST /api/v2/organize/duplicate
{
  "paths": ["/music/library"]
}

Response:
{
  "duplicates": [
    {
      "files": [
        "/music/library/song1.mp3",
        "/music/library/song2.mp3"
      ],
      "size": 5000000,
      "hash": "abc123"
    }
  ]
}
```

## MediaServer Module API

### 获取可用设备
```
GET /api/v2/mediaserver/devices

Response:
{
  "devices": [
    {
      "id": "device-uuid",
      "name": "Living Room TV",
      "type": "chromecast",
      "status": "idle"
    },
    {
      "id": "device-uuid-2",
      "name": "Smart Speaker",
      "type": "dlna",
      "status": "playing"
    }
  ]
}
```

### 投放到设备
```
POST /api/v2/mediaserver/cast
{
  "device_id": "device-uuid",
  "track_id": 123,
  "playback": {
    "position": 0,
    "volume": 80
  }
}

Response:
{
  "session_id": "session-123",
  "status": "playing"
}
```

### 控制播放
```
POST /api/v2/mediaserver/{session_id}/control
{
  "action": "pause"  // play, pause, stop, seek
}

Response:
{
  "status": "paused"
}
```

### 获取转码状态
```
GET /api/v2/mediaserver/transcode/{task_id}

Response:
{
  "task_id": "task-123",
  "status": "completed",
  "output_url": "https://..."
}
```

## 错误响应格式

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Invalid parameter: chart_id"
  }
}
```

### 错误代码
| 代码 | 描述 |
|------|------|
| INVALID_REQUEST | 请求参数无效 |
| NOT_FOUND | 资源不存在 |
| DEVICE_OFFLINE | 设备离线 |
| TRANSCODING_FAILED | 转码失败 |