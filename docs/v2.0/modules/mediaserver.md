# MediaServer Module 设计

## 📋 模块概述

MediaServer Module 提供 DLNA/UPnP 和 Chromecast 媒体服务器功能，支持本地音乐串流到多设备播放。

## 🎯 功能需求

1. **DLNA 服务**: 作为 DLNA/DMR (Digital Media Renderer)
2. **设备发现**: 自动发现局域网内播放设备
3. **投屏控制**: 控制 Chromecast 设备播放
4. **转码支持**: 多种音频格式转码

## 🏗️ 架构设计

```
                    ┌─────────────┐
                    │  FastAPI    │
                    │  Backend    │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐      ┌─────▼─────┐     ┌─────▼─────┐
    │  DLNA   │      │Chromecast │     │Transcoder │
    │ Server  │      │  Client   │     │  (FFmpeg) │
    └────┬────┘      └─────┬─────┘     └─────┬─────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Network    │
                    │  (LAN)      │
                    └─────────────┘
```

## 🔌 核心组件

### DlnaServer
```python
class DlnaServer:
    # HTTP Server
    - port: 8200
    - serve_content: 音频文件 HTTP 访问
    
    # SOAP Server  
    - AVTransport: 播放控制
    - ConnectionManager: 连接管理
    - RenderingControl: 渲染控制
    
    # SSDP/UDP
    - 设备公告
    - 发现响应
```

### DeviceDiscovery
```python
class DeviceDiscovery:
    # SSDP 监听
    - multicast: 239.255.255.250:1900
    
    # 设备缓存
    - device_list: List[Device]
    - heartbeat: 定期检查设备状态
    
    # 设备类型
    - urn:schemas-upnp-org:device:MediaRenderer:1
```

### ChromecastClient
```python
class ChromecastController:
    # 连接
    - discover(): 查找设备
    - connect(device_id): 建立连接
    
    # 播放控制
    - load(media_url, content_type)
    - play(), pause(), stop()
    - seek(position)
    - set_volume(level)
    
    # 媒体信息
    - get_status(): 获取播放状态
```

### Transcoder
```python
class AudioTranscoder:
    # 支持格式
    - input: mp3, flac, wav, aac, ogg
    - output: mp3 (streaming), aac
    
    # 质量选项
    - bitrate: 128k, 192k, 320k
    - sample_rate: 44100, 48000
    
    # 特性
    - stream_mode: 流式转码
    - on_the_fly: 即时转码
```

## 📡 DLNA 服务

### 设备描述 (XML)
```xml
<device>
  <deviceType>urn:schemas-upnp-org:device:MediaRenderer:1</deviceType>
  <friendlyName>MusicPilot</friendlyName>
  <manufacturer>MusicPilot</manufacturer>
  <modelName>MusicPilot DLNA</modelName>
</device>
```

### 支持的 SOAP Actions
- `SetAVTransportURI`
- `Play`
- `Pause`
- `Stop`
- `Seek`
- `GetPositionInfo`
- `GetTransportInfo`

## 🎮 Chromecast 协议

### Media Message
```json
{
  "type": "LOAD",
  "media": {
    "contentId": "http://192.168.1.100:8200/track/123",
    "streamType": "BUFFERED",
    "metadata": {
      "title": "Song Title",
      "artist": "Artist Name",
      "albumArt": "http://..."
    }
  }
}
```

## 🔐 安全考虑

- 局域网访问控制
- HTTPS (可选)
- 设备认证 (可选)
- 防火墙规则建议