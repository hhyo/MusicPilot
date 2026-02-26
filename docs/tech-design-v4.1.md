# MusicPilot - 订阅下载架构设计 v4.1（融合版）

> **版本**: v4.1（融合版）
> **变更**: 融合 M5 订阅功能（艺术家/专辑）+ M4 资源站点搜索/下载器对接
> **最后更新**: 2026-02-26

---

## 1. 订阅类型（融合）

MusicPilot 支持**三种订阅类型**：

### 1.1 订阅艺术家（Artist）
- **来源**：MusicBrainz
- **触发**：艺术家发布新专辑
- **流程**：
  ```
  查询 MusicBrainz -> 发现新专辑 -> 资源站点搜索 -> 推送下载
  ```

### 1.2 订阅专辑（Album）
- **来源**：MusicBrainz
- **触发**：专辑有新版本（重制版、扩展版等）
- **流程**：
  ```
  查询 MusicBrainz -> 发现新版本 -> 资源站点搜索 -> 推送下载
  ```

### 1.3 订阅歌单/榜单（Playlist/Chart）
- **来源**：网易云音乐、QQ音乐
- **触发**：歌单/榜单有新内容
- **流程**：
  ```
  抓取歌单/榜单 -> 提取曲目列表 -> 资源站点搜索 -> 推送下载
  ```

---

## 2. 工作流程融合

### 2.1 订阅艺术家流程

```
1. 定时任务触发
   ↓
2. 查询 MusicBrainz 艺术家作品列表
   - 获取艺术家所有专辑
   - 按发布日期排序
   ↓
3. 检查是否有新专辑
   - 对比本地数据库的最后发布时间
   ↓
4. 发现新专辑
   ↓
5. 从资源站点搜索种子
   - 搜索关键词：{艺术家} {专辑}
   - 并发搜索多个站点
   ↓
6. 匹配订阅规则
   - 音质（FLAC/320k）
   - 站点优先级
   - 大小限制
   ↓
7. 推送种子到下载器
   - qBittorrent / Transmission
   ↓
8. 发送订阅事件
   - SubscribeNewRelease
   - DownloadStarted
```

### 2.2 订阅专辑流程

```
1. 定时任务触发
   ↓
2. 查询 MusicBrainz 专辑信息
   - 获取专辑的所有版本
   ↓
3. 检查是否有新版本
   - 对比本地数据库的版本信息
   ↓
4. 发现新版本
   ↓
5. 从资源站点搜索种子
   - 搜索关键词：{艺术家} {专辑} {版本}
   ↓
6. 匹配订阅规则
   ↓
7. 推送种子到下载器
   ↓
8. 发送订阅事件
```

### 2.3 订阅歌单/榜单流程

```
1. 定时任务触发
   ↓
2. 抓取歌单/榜单信息
   - 网易云音乐歌单 API
   - QQ音乐榜单 API
   ↓
3. 提取曲目列表
   - 艺术家 + 专辑 + 曲目
   - 格式化搜索关键词
   ↓
4. 对每个曲目检查是否已下载
   ↓
5. 从资源站点搜索种子
   - 搜索关键词：{艺术家} {专辑}
   ↓
6. 匹配订阅规则
   ↓
7. 推送种子到下载器
   ↓
8. 发送订阅事件
```

---

## 3. 数据库模型（融合）

### 3.1 Subscribe 订阅模型（保留之前 M5 设计，需扩展）

```python
class Subscribe(Base, TimestampMixin):
    """订阅模型"""
    __tablename__ = "subscribes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 订阅类型（扩展）
    type: Mapped[str] = mapped_column(String(50))  # artist, album, playlist, chart

    # 来源类型
    source_type: Mapped[str] = mapped_column(String(50))  # musicbrainz, netease, qq

    # 源ID（扩展支持）
    # - artist/album: MusicBrainz ID
    # - playlist/chart: 歌单ID/榜单ID
    musicbrainz_id: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    playlist_id: Mapped[str] = mapped_column(String(100), nullable=True)  # 网易云/QQ歌单ID

    # 名称
    name: Mapped[str] = mapped_column(String(255))

    # 描述
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # 订阅规则（JSON）
    rules: Mapped[dict] = mapped_column(JSON, nullable=True)
    # {
    #   "quality": "flac",  # flac, 320k, standard
    #   "sites": [1, 2, 3],  # 站点ID列表
    #   "min_size": 100 * 1024 * 1024,  # 最小大小
    #   "max_size": 1024 * 1024 * 1024,  # 最大大小
    #   "free_only": False,  # 只要免费资源
    #   "include_singles": False,  # 是否包含单曲（仅专辑订阅）
    # }

    # 下载器配置
    downloader: Mapped[str] = mapped_column(String(50), default="qbittorrent")
    save_path: Mapped[str] = mapped_column(String(500), nullable=True)

    # 是否启用
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # 自动下载
    auto_download: Mapped[bool] = mapped_column(Boolean, default=True)

    # 下载格式
    download_format: Mapped[str] = mapped_column(String(50), default="flac")

    # 最后检查时间
    last_check: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # 最后发布时间
    last_release: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # 发布数量
    release_count: Mapped[int] = mapped_column(Integer, default=0)

    # 订阅状态
    state: Mapped[str] = mapped_column(String(50), default="active")  # active, paused, completed
```

### 3.2 SubscribeRelease 订阅发布记录（新增）

```python
class SubscribeRelease(Base, TimestampMixin):
    """订阅发布记录模型"""
    __tablename__ = "subscribe_releases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 关联订阅
    subscribe_id: Mapped[int] = mapped_column(Integer, ForeignKey("subscribes.id"), index=True)

    # 发布类型
    release_type: Mapped[str] = mapped_column(String(50))  # album, playlist_update

    # 音乐信息
    artist: Mapped[str] = mapped_column(String(255), nullable=True)
    album: Mapped[str] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=True)

    # MusicBrainz 信息
    musicbrainz_id: Mapped[str] = mapped_column(String(100), nullable=True)

    # 发布时间
    release_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # 下载状态
    download_status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, downloading, completed, failed

    # 种子信息
    torrent_id: Mapped[str] = mapped_column(String(100), nullable=True)
    torrent_site: Mapped[str] = mapped_column(String(100), nullable=True)
    torrent_size: Mapped[int] = mapped_column(BigInteger, nullable=True)

    # 下载器任务ID
    downloader_task_id: Mapped[str] = mapped_column(String(100), nullable=True)

    # 错误信息
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
```

### 3.3 Site 资源站点模型（新增）

```python
class Site(Base, TimestampMixin):
    """资源站点模型"""
    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 基本信息
    name: Mapped[str] = mapped_column(String(255))
    domain: Mapped[str] = mapped_column(String(255), nullable=True)
    url: Mapped[str] = mapped_column(String(500))

    # 认证信息
    cookie: Mapped[str] = mapped_column(Text, nullable=True)
    passkey: Mapped[str] = mapped_column(String(100), nullable=True)
    username: Mapped[str] = mapped_column(String(100), nullable=True)
    password: Mapped[str] = mapped_column(String(100), nullable=True)

    # 连接配置
    proxy: Mapped[str] = mapped_column(String(500), nullable=True)
    ua: Mapped[str] = mapped_column(String(500), nullable=True)
    timeout: Mapped[int] = mapped_column(Integer, default=30)

    # RSS 配置
    rss: Mapped[str] = mapped_column(String(500), nullable=True)
    rss_interval: Mapped[int] = mapped_column(Integer, default=60)

    # 下载器配置
    downloader: Mapped[str] = mapped_column(String(50), default="qbittorrent")

    # 优先级
    priority: Mapped[int] = mapped_column(Integer, default=1)

    # 是否启用
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # 站点类型
    site_type: Mapped[str] = mapped_column(String(50), default="resource")  # resource, other
```

### 3.4 DownloadHistory 下载历史模型（更新）

```python
class DownloadHistory(Base, TimestampMixin):
    """下载历史模型"""
    __tablename__ = "download_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 来源
    source: Mapped[str] = mapped_column(String(50))  # subscribe, manual, site_rss
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("subscribes.id"), nullable=True)

    # 种子信息
    torrent_id: Mapped[str] = mapped_column(String(100))

    # 站点信息
    site: Mapped[str] = mapped_column(String(100))

    # 音乐信息
    title: Mapped[str] = mapped_column(String(255))
    artist: Mapped[str] = mapped_column(String(255), nullable=True)
    album: Mapped[str] = mapped_column(String(255), nullable=True)

    # 种子信息
    size: Mapped[int] = mapped_column(BigInteger)
    quality: Mapped[str] = mapped_column(String(50), nullable=True)

    # 下载器信息
    downloader: Mapped[str] = mapped_column(String(50))
    task_id: Mapped[str] = mapped_column(String(100))

    # 下载状态
    status: Mapped[str] = mapped_column(String(50))

    # 进度信息
    progress: Mapped[float] = mapped_column(Float, default=0)
    download_speed: Mapped[int] = mapped_column(BigInteger, nullable=True)
    eta: Mapped[int] = mapped_column(Integer, nullable=True)

    # 文件路径
    file_path: Mapped[str] = mapped_column(String(1000), nullable=True)

    # 错误信息
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    # 完成时间
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
```

---

## 4. Chain 层设计（融合）

### 4.1 SubscribeChain 订阅链（重新实现）

```python
class SubscribeChain(ChainBase):
    """订阅链"""

    async def check_artist(self, subscribe_id: int):
        """检查艺术家订阅

        Args:
            subscribe_id: 订阅ID

        流程：
        1. 查询 MusicBrainz 艺术家作品列表
        2. 检查是否有新专辑
        3. 对每个新专辑搜索种子
        4. 匹配规则并推送下载
        """
        # 获取订阅
        subscribe = await self.subscribe_oper.get(subscribe_id)
        if not subscribe or subscribe.type != "artist":
            return

        # 查询 MusicBrainz
        albums = await self.run_module(
            "musicbrainz", "get_artist_discography",
            musicbrainz_id=subscribe.musicbrainz_id
        )

        # 过滤新专辑
        new_albums = self.filter_new_albums(albums, subscribe.last_release)

        if not new_albums:
            self.logger.info(f"艺术家 {subscribe.name} 没有新专辑")
            return

        self.logger.info(f"艺术家 {subscribe.name} 发现 {len(new_albums)} 个新专辑")

        # 处理每个新专辑
        for album in new_albums:
            await self.process_album(subscribe, album)

        # 更新最后检查时间
        await self.subscribe_oper.update(
            subscribe_id,
            last_check=datetime.now(),
        )

    async def check_album(self, subscribe_id: int):
        """检查专辑订阅"""
        subscribe = await self.subscribe_oper.get(subscribe_id)
        if not subscribe or subscribe.type != "album":
            return

        # 查询 MusicBrainz 专辑版本
        versions = await self.run_module(
            "musicbrainz", "get_album_versions",
            musicbrainz_id=subscribe.musicbrainz_id
        )

        # 过滤新版本
        new_versions = self.filter_new_versions(versions, subscribe.last_release)

        if not new_versions:
            return

        # 处理每个新版本
        for version in new_versions:
            await self.process_album(subscribe, version)

        await self.subscribe_oper.update(subscribe_id, last_check=datetime.now())

    async def check_playlist(self, subscribe_id: int):
        """检查歌单/榜单订阅"""
        subscribe = await self.subscribe_oper.get(subscribe_id)
        if not subscribe or subscribe.type not in ["playlist", "chart"]:
            return

        # 根据来源抓取歌单
        if subscribe.source_type == "netease":
            tracks = await self.run_module(
                "netease", "fetch_playlist",
                playlist_id=subscribe.playlist_id
            )
        elif subscribe.source_type == "qq":
            tracks = await self.run_module(
                "qq", "fetch_chart",
                chart_id=subscribe.playlist_id
            )
        else:
            return

        # 处理每个曲目
        for track in tracks:
            # 检查是否已下载
            exists = await self.check_track_exists(track)
            if exists:
                continue

            # 搜索种子
            keyword = f"{track['artist']} {track['album']}"
            torrents = await self.run_module(
                "torrents", "search",
                keyword=keyword,
                category="music",
            )

            # 匹配规则
            matched = self.match_rules(torrents, subscribe.rules)
            if matched:
                # 创建发布记录
                release = await self.subscribe_release_oper.create(
                    subscribe_id=subscribe_id,
                    release_type="playlist_update",
                    artist=track["artist"],
                    album=track["album"],
                    title=track["title"],
                )

                # 推送下载
                await self.push_download(subscribe, matched, release.id)

        await self.subscribe_oper.update(subscribe_id, last_check=datetime.now())

    async def process_album(self, subscribe: Subscribe, album: dict):
        """处理专辑（搜索并下载）"""
        # 搜索种子
        keyword = f"{album['artist']} {album['title']}"
        torrents = await self.run_module(
            "torrents", "search",
            keyword=keyword,
            category="music",
        )

        # 匹配规则
        matched = self.match_rules(torrents, subscribe.rules)
        if not matched:
            self.logger.warning(f"专辑 {album['title']} 没有匹配的种子")
            return

        # 创建发布记录
        release = await self.subscribe_release_oper.create(
            subscribe_id=subscribe.id,
            release_type="album",
            artist=album["artist"],
            album=album["title"],
            release_date=album["release_date"],
            musicbrainz_id=album.get("musicbrainz_id"),
        )

        # 推送下载
        await self.push_download(subscribe, matched, release.id)

        # 更新订阅最后发布时间
        await self.subscribe_oper.update(
            subscribe.id,
            last_release=album["release_date"],
            release_count=(subscribe.release_count or 0) + 1,
        )

    async def push_download(self, subscribe: Subscribe, torrent, release_id: int):
        """推送下载"""
        # 推送到下载器
        task_id = await self.run_module(
            "downloader", "push_torrent",
            torrent=torrent,
            downloader=subscribe.downloader,
            save_path=subscribe.save_path,
        )

        # 更新发布记录
        await self.subscribe_release_oper.update(
            release_id,
            download_status="downloading",
            torrent_id=torrent.enclosure,
            torrent_site=torrent.site_name,
            torrent_size=torrent.size,
            downloader_task_id=task_id,
        )

        # 发送事件
        await self.put_message(
            EventType.SubscribeNewRelease,
            {
                "subscribe_id": subscribe.id,
                "release_id": release_id,
                "torrent": torrent,
                "task_id": task_id,
            }
        )

    def filter_new_albums(self, albums: List[dict], last_release: datetime = None) -> List[dict]:
        """过滤新专辑"""
        if not last_release:
            return albums

        new_albums = [
            album for album in albums
            if album.get("release_date") and album["release_date"] > last_release
        ]
        return new_albums

    def filter_new_versions(self, versions: List[dict], last_release: datetime = None) -> List[dict]:
        """过滤新版本"""
        # 类似 filter_new_albums
        pass

    def match_rules(self, torrents: List[TorrentInfo], rules: dict) -> Optional[TorrentInfo]:
        """匹配订阅规则"""
        filtered = torrents

        # 过滤音质
        if "quality" in rules:
            quality_map = {"flac": "FLAC", "320k": "MP3-320k", "standard": "MP3-128k"}
            target_quality = quality_map.get(rules["quality"])
            if target_quality:
                filtered = [t for t in filtered if target_quality in t.title]

        # 过滤站点
        if "sites" in rules:
            filtered = [t for t in filtered if t.site_id in rules["sites"]]

        # 过滤大小
        if "min_size" in rules:
            filtered = [t for t in filtered if t.size >= rules["min_size"]]

        if "max_size" in rules:
            filtered = [t for t in filtered if t.size <= rules["max_size"]]

        # 只要免费资源
        if rules.get("free_only"):
            filtered = [t for t in filtered if t.free]

        # 按优先级排序
        filtered.sort(key=lambda x: x.site_priority, reverse=True)

        return filtered[0] if filtered else None

    async def check_track_exists(self, track: dict) -> bool:
        """检查曲目是否已下载"""
        # 检查数据库是否有相同曲目
        existing = await self.track_oper.get_by_artist_album_title(
            track["artist"],
            track["album"],
            track["title"]
        )
        return existing is not None

    async def check_all(self):
        """检查所有订阅"""
        subscribes = await self.subscribe_oper.get_active()

        for subscribe in subscribes:
            if not subscribe.auto_download:
                continue

            try:
                if subscribe.type == "artist":
                    await self.check_artist(subscribe.id)
                elif subscribe.type == "album":
                    await self.check_album(subscribe.id)
                elif subscribe.type in ["playlist", "chart"]:
                    await self.check_playlist(subscribe.id)
            except Exception as e:
                self.logger.error(f"检查订阅失败: {subscribe.name}, 错误: {e}")
```

---

## 5. 任务里程碑更新（融合）

### M4: 资源站点和下载器对接（新增）

| 任务 | 描述 | 预计工时 |
|------|------|----------|
| M4-T1 | 资源站点数据模型（Site） | 3h |
| M4-T2 | TorrentsChain 资源链 | 8h |
| M4-T3 | 站点模块（站点搜索实现） | 10h |
| M4-T4 | DownloaderChain 下载器链 | 6h |
| M4-T5 | 下载器对接模块（qBittorrent/Transmission） | 6h |
| M4-T6 | 前端站点管理界面 | 6h |
| M4-T7 | 下载进度监控任务 | 2h |

### M5: 订阅功能（融合之前的艺术家/专辑 + 新的歌单/榜单）

| 任务 | 描述 | 预计工时 |
|------|------|----------|
| M5-T1 | 订阅数据模型（扩展支持歌单/榜单） | 2h |
| M5-T2 | SubscribeRelease 发布记录模型 | 2h |
| M5-T3 | SubscribeChain 订阅链（融合三种类型） | 10h |
| M5-T4 | 歌单/榜单抓取模块（网易云音乐/QQ音乐） | 6h |
| M5-T5 | 订阅定时任务 | 2h |
| M5-T6 | 前端订阅管理界面 | 6h |

---

## 6. 需要删除的代码

### 完全删除（之前的错误实现）

```bash
# 下载器模块（完全删除）
rm -rf backend/app/modules/downloader/

# 下载链（完全删除）
rm backend/app/chain/download.py
```

### 保留并融合

```bash
# 订阅链（保留，需重新实现）
# backend/app/chain/subscribe.py

# 整理链（保留，需适配）
# backend/app/chain/transfer.py
```

---

## 7. 前端页面融合

### 订阅管理页面（融合三种订阅类型）

```
┌─────────────────────────────────────────────────────────────┐
│ 订阅管理                                    [添加订阅] [全部刷新]│
├─────────────────────────────────────────────────────────────┤
│ ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐       │
│ │名称  │类型  │来源  │状态  │规则  │最后检查│操作 │      │
│ ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤       │
│ │周杰伦│艺术家│MB   │ ✅  │FLAC  │10分钟前│编辑 │      │
│ │      │      │      │     │站点1 │        │删除 │      │
│ ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤       │
│ │经典  │专辑  │MB   │ ✅  │320k  │5分钟前 │编辑 │      │
│ │金曲  │      │      │     │所有站点│        │删除 │      │
│ ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤       │
│ │热歌   │歌单 │网云│ ✅  │FLAC  │1小时前│编辑 │      │
│ │榜     │      │音乐 │     │站点2 │        │删除 │      │
│ ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤       │
│ │巅峰  │榜单 │QQ   │ ✅  │标准  │2小时前│编辑 │      │
│ │榜     │      │音乐 │     │所有站点│        │删除 │      │
│ └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. 总结

### 融合点

1. **之前的订阅设计**（保留）
   - ✅ 订阅艺术家
   - ✅ 订阅专辑
   - ✅ MusicBrainz 查询

2. **新增的订阅类型**
   - ✅ 订阅歌单
   - ✅ 订阅榜单

3. **资源站点搜索和下载器对接**（新增）
   - ✅ TorrentsChain 资源链
   - ✅ DownloaderChain 下载器链
   - ✅ qBittorrent/Transmission 对接

### 统一的工作流程

所有三种订阅类型都遵循统一的工作流程：
```
检查更新 -> 资源站点搜索 -> 匹配规则 -> 推送下载 -> 监控进度 -> 整理文件
```