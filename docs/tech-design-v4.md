# MusicPilot - 订阅下载架构设计 v4.0

> **版本**: v4.0
> **基于**: 用户反馈（订阅歌单/榜单 + PT站点搜索 + 下载器对接）
> **最后更新**: 2026-02-26

---

## 1. 架构概述

### 1.1 核心原则

**MusicPilot 不直接下载音乐文件**，而是作为一个"协调者"：

1. **订阅源抓取**：从网易云音乐/QQ音乐等平台抓取歌单/榜单信息
2. **PT站点管理**：管理音乐PT站点，搜索种子文件
3. **下载器对接**：推送种子到 qBittorrent/Transmission
4. **进度监控**：从下载器获取下载进度和状态
5. **文件整理**：下载完成后整理目录结构并补全元数据

### 1.2 系统边界

```
┌─────────────────────────────────────────────────────────────────┐
│                        MusicPilot                               │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ 订阅源   │ -> │ PT站点   │ -> │ 下载器   │ -> │  文件    │  │
│  │ 管理模块 │    │ 搜索模块 │    │ 对接模块 │    │  整理    │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│       |               |               |               |        │
│       | 抓取歌单      | 搜索种子      | 推送种子      | 整理     │
│       |               |               |               |        │
│       v               v               v               v        │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ 网易云   │    │ M-Team   │    │ qBittor- │    │ Artist/  │  │
│  │ 音乐     │    │ HDChina  │    │ rent      │    │ Album/  │  │
│  │ QQ音乐   │    │ SSL      │    │ Transmis- │    │ Track   │  │
│  │ ...      │    │ ...      │    │ sion      │    │ .mp3     │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 工作流程

### 2.1 订阅源刷新流程

```
1. 定时任务触发
   ↓
2. 抓取订阅源（歌单/榜单）
   - 网易云音乐歌单 API
   - QQ音乐榜单 API
   ↓
3. 提取音乐列表
   - 艺术家 + 专辑 + 曲目
   - 格式化搜索关键词
   ↓
4. 从PT站点搜索种子
   - 并发搜索多个站点
   - 过滤（音质、大小、编码）
   ↓
5. 命中规则检查
   - 检查是否已下载
   - 检查订阅规则
   ↓
6. 推送种子到下载器
   - qBittorrent / Transmission
   ↓
7. 发送订阅事件
   - SubscribeNewRelease
   - DownloadStarted
```

### 2.2 下载进度监控流程

```
1. 定时任务触发（每分钟）
   ↓
2. 查询下载器状态
   - qBittorrent API
   - Transmission RPC
   ↓
3. 获取下载进度
   - 下载速度
   - 已下载大小
   - ETA
   ↓
4. 更新下载历史记录
   ↓
5. 检查下载完成
   - 监控下载器完成事件
   ↓
6. 触发文件整理
   - 调用 TransferChain
   - 整理目录结构
   - 补全元数据
   ↓
7. 发送完成事件
   - DownloadCompleted
   - TransferCompleted
```

---

## 3. Chain 层设计

### 3.1 SubscribeChain（订阅链）

**职责**：管理订阅源，抓取歌单/榜单，触发搜索和下载

```python
class SubscribeChain(ChainBase):
    """订阅链"""

    async def refresh_source(self, source_id: int):
        """刷新订阅源

        Args:
            source_id: 订阅源 ID

        流程：
        1. 从数据库获取订阅源配置
        2. 根据类型抓取歌单/榜单
        3. 提取音乐列表
        4. 调用 TorrentsChain 搜索种子
        5. 检查命中规则
        6. 推送到下载器
        """
        # 获取订阅源
        source = await self.subscribe_oper.get(source_id)
        if not source:
            return

        # 根据类型抓取
        if source.type == SourceType.NETEASE_PLAYLIST:
            tracks = await self.run_module(
                "netease", "fetch_playlist", source.source_id
            )
        elif source.type == SourceType.QQ_CHART:
            tracks = await self.run_module(
                "qq", "fetch_chart", source.source_id
            )
        else:
            return

        # 提取音乐列表并搜索种子
        for track in tracks:
            # 检查是否已下载
            exists = await self.check_exists(track)
            if exists:
                continue

            # 搜索种子
            torrents = await self.run_module(
                "torrents", "search",
                keyword=f"{track.artist} {track.album}",
                category="music",
            )

            # 命中规则检查
            matched = self.match_rules(torrents, source.rules)
            if matched:
                # 推送到下载器
                await self.run_module(
                    "downloader", "push_torrent",
                    torrent=matched,
                    downloader=source.downloader
                )

                # 发送事件
                await self.put_message(
                    EventType.SubscribeNewRelease,
                    {
                        "source_id": source.id,
                        "track": track,
                        "torrent": matched,
                    }
                )

    async def refresh_all(self):
        """刷新所有订阅源"""
        sources = await self.subscribe_oper.get_active()
        for source in sources:
            await self.refresh_source(source.id)

    def check_exists(self, track) -> bool:
        """检查是否已下载"""
        # 检查本地是否已有该曲目
        return False

    def match_rules(self, torrents: List[TorrentInfo], rules: dict) -> Optional[TorrentInfo]:
        """匹配订阅规则

        规则包括：
        - 站点优先级
        - 音质要求（FLAC/320k/无损）
        - 大小限制
        - 免费/促销
        """
        filtered = torrents

        # 过滤音质
        if "quality" in rules:
            filtered = [t for t in filtered if t.quality == rules["quality"]]

        # 过滤站点
        if "sites" in rules:
            filtered = [t for t in filtered if t.site in rules["sites"]]

        # 过滤大小
        if "min_size" in rules:
            filtered = [t for t in filtered if t.size >= rules["min_size"]]

        if "max_size" in rules:
            filtered = [t for t in filtered if t.size <= rules["max_size"]]

        # 按优先级排序
        filtered.sort(key=lambda x: x.site_order, reverse=True)

        return filtered[0] if filtered else None
```

### 3.2 TorrentsChain（资源链）

**职责**：管理PT站点，搜索种子，下载种子文件

```python
class TorrentsChain(ChainBase):
    """资源链"""

    async def search(
        self,
        keyword: str,
        sites: List[int] = None,
        category: str = "music",
        filters: dict = None
    ) -> List[TorrentInfo]:
        """在PT站点搜索种子

        Args:
            keyword: 搜索关键词（艺术家/专辑）
            sites: 站点ID列表，为空则搜索所有
            category: 分类（music/flac/lossless）
            filters: 过滤条件

        Returns:
            TorrentInfo 列表
        """
        results = []

        # 获取要搜索的站点
        if sites:
            site_list = [await self.site_oper.get(s) for s in sites]
        else:
            site_list = await self.site_oper.get_active()

        # 并发搜索
        for site in site_list:
            if not site.enabled:
                continue

            try:
                site_results = await self.run_module(
                    "search_torrents",
                    site=site,
                    keyword=keyword,
                    category=category,
                    filters=filters or {}
                )
                results.extend(site_results)
            except Exception as e:
                self.logger.error(f"站点 {site.name} 搜索失败：{e}")

        # 去重
        results = self.deduplicate(results)

        return results

    async def download_torrent(self, torrent: TorrentInfo) -> str:
        """下载种子文件

        Args:
            torrent: TorrentInfo 对象

        Returns:
            种子文件路径
        """
        site = await self.site_oper.get(torrent.site_id)

        # 下载种子
        torrent_bytes = await self.run_module(
            "download_torrent",
            site=site,
            torrent=torrent
        )

        # 保存种子文件
        from pathlib import Path
        torrent_dir = Path(settings.torrent_path)
        torrent_dir.mkdir(parents=True, exist_ok=True)

        # 生成安全文件名
        safe_name = self.sanitize_filename(torrent.title)
        torrent_path = torrent_dir / f"{safe_name}.torrent"

        with open(torrent_path, "wb") as f:
            f.write(torrent_bytes)

        return str(torrent_path)

    def deduplicate(self, torrents: List[TorrentInfo]) -> List[TorrentInfo]:
        """去重"""
        seen = set()
        unique = []

        for torrent in torrents:
            # 使用标题 + 大小作为去重键
            key = f"{torrent.title}_{torrent.size}"
            if key not in seen:
                seen.add(key)
                unique.append(torrent)

        return unique

    def sanitize_filename(self, filename: str) -> str:
        """清理文件名"""
        import re
        safe = re.sub(r'[<>:"/\\|?*]', '', filename)
        return safe.strip()
```

### 3.3 DownloaderChain（下载器链）

**职责**：对接 qBittorrent/Transmission，推送种子，获取下载进度

```python
class DownloaderChain(ChainBase):
    """下载器链"""

    async def push_torrent(
        self,
        torrent: TorrentInfo,
        downloader: str = "qbittorrent",
        save_path: str = None
    ) -> str:
        """推送种子到下载器

        Args:
            torrent: TorrentInfo 对象
            downloader: 下载器类型（qbittorrent/transmission）
            save_path: 保存路径

        Returns:
            下载任务ID
        """
        # 下载种子文件
        torrent_path = await self.run_module(
            "torrents", "download_torrent", torrent
        )

        # 推送到下载器
        if downloader == "qbittorrent":
            task_id = await self.run_module(
                "qbittorrent", "add_torrent",
                torrent_file=torrent_path,
                save_path=save_path,
                tags=["musicpilot"]
            )
        elif downloader == "transmission":
            task_id = await self.run_module(
                "transmission", "add_torrent",
                torrent_file=torrent_path,
                download_dir=save_path
            )
        else:
            raise ValueError(f"不支持的下载器: {downloader}")

        # 创建下载记录
        await self.download_history_oper.create(
            source="pt",
            source_id=torrent.title,
            torrent_id=torrent.enclosure,
            site=torrent.site_name,
            title=torrent.title,
            size=torrent.size,
            quality=torrent.quality,
            downloader=downloader,
            status="downloading",
        )

        # 发送事件
        await self.put_message(
            EventType.DownloadStarted,
            {
                "task_id": task_id,
                "torrent": torrent,
                "downloader": downloader,
            }
        )

        return task_id

    async def get_download_status(self, task_id: str, downloader: str) -> dict:
        """获取下载状态

        Args:
            task_id: 任务ID
            downloader: 下载器类型

        Returns:
            下载状态信息
        """
        if downloader == "qbittorrent":
            status = await self.run_module(
                "qbittorrent", "get_torrent_status", task_id
            )
        elif downloader == "transmission":
            status = await self.run_module(
                "transmission", "get_torrent_status", task_id
            )
        else:
            raise ValueError(f"不支持的下载器: {downloader}")

        # 更新数据库
        await self.download_history_oper.update(
            task_id,
            progress=status["progress"],
            download_speed=status["download_speed"],
            eta=status["eta"],
        )

        return status

    async def check_completed(self, downloader: str):
        """检查下载完成的任务"""
        if downloader == "qbittorrent":
            completed = await self.run_module(
                "qbittorrent", "get_completed_torrents"
            )
        elif downloader == "transmission":
            completed = await self.run_module(
                "transmission", "get_completed_torrents"
            )

        for task in completed:
            # 更新状态
            await self.download_history_oper.update(
                task["hash"],
                status="completed",
                file_path=task["save_path"],
            )

            # 触发文件整理
            await self.run_module(
                "transfer", "organize_download",
                task=task,
            )

            # 发送完成事件
            await self.put_message(
                EventType.DownloadCompleted,
                {
                    "task_id": task["hash"],
                    "title": task["name"],
                    "save_path": task["save_path"],
                }
            )
```

### 3.4 TransferChain（整理链 - 已有，需适配）

**职责**：下载完成后整理目录结构，补全元数据

与之前的 M4-T4 类似，但需要适配从下载器获取的文件。

---

## 4. Module 层设计

### 4.1 订阅源模块（新增）

```python
class NeteasePlaylistModule:
    """网易云音乐歌单模块"""

    async def fetch_playlist(self, playlist_id: str) -> List[dict]:
        """抓取歌单

        Args:
            playlist_id: 歌单ID

        Returns:
            曲目列表 [{artist, album, title}, ...]
        """
        # 调用网易云音乐API
        url = f"https://music.163.com/api/playlist/detail?id={playlist_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            data = response.json()

        tracks = []
        for track in data.get("playlist", {}).get("tracks", []):
            tracks.append({
                "artist": track.get("ar", [{}])[0].get("name"),
                "album": track.get("al", {}).get("name"),
                "title": track.get("name"),
            })

        return tracks


class QQChartModule:
    """QQ音乐榜单模块"""

    async def fetch_chart(self, chart_id: str) -> List[dict]:
        """抓取榜单"""
        # 调用QQ音乐API
        # ...
        return tracks
```

### 4.2 PT站点模块（重新设计）

```python
class SiteModule:
    """PT站点模块 - 基础类"""

    async def search_torrents(
        self,
        site: Site,
        keyword: str,
        category: str = None,
        filters: dict = None
    ) -> List[TorrentInfo]:
        """搜索种子"""
        # 各站点继承实现自己的搜索逻辑
        pass

    async def download_torrent(self, site: Site, torrent: TorrentInfo) -> bytes:
        """下载种子文件"""
        # 使用站点Cookie和UA下载
        pass
```

### 4.3 下载器模块（新增）

```python
class QbittorrentModule:
    """qBittorrent 模块"""

    async def add_torrent(
        self,
        torrent_file: str,
        save_path: str = None,
        tags: List[str] = None
    ) -> str:
        """添加种子"""
        # 调用 qBittorrent Web API
        url = f"{settings.qbittorrent_url}/api/v2/torrents/add"

        with open(torrent_file, "rb") as f:
            files = {"torrents": f}
            data = {
                "savepath": save_path,
                "tags": ",".join(tags or []),
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    files=files,
                    data=data,
                    auth=(settings.qbittorrent_username, settings.qbittorrent_password)
                )

        return response.json().get("hash")

    async def get_torrent_status(self, hash: str) -> dict:
        """获取种子状态"""
        url = f"{settings.qbittorrent_url}/api/v2/torrents/info"
        params = {"hashes": hash}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                auth=(settings.qbittorrent_username, settings.qbittorrent_password)
            )

        torrent = response.json()[0]
        return {
            "progress": torrent["progress"],
            "download_speed": torrent["dl_speed"],
            "eta": torrent["eta"],
            "save_path": torrent["save_path"],
        }


class TransmissionModule:
    """Transmission 模块"""

    async def add_torrent(self, torrent_file: str, download_dir: str = None) -> str:
        """添加种子"""
        # 调用 Transmission RPC
        pass

    async def get_torrent_status(self, hash: str) -> dict:
        """获取种子状态"""
        # 调用 Transmission RPC
        pass
```

---

## 5. 数据库模型（更新）

### 5.1 订阅源模型（更新）

```python
class SubscribeSource(Base, TimestampMixin):
    """订阅源模型"""
    __tablename__ = "subscribe_sources"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 订阅源类型
    type: Mapped[str] = mapped_column(String(50))  # netease_playlist, qq_chart, etc.

    # 源ID（歌单ID、榜单ID等）
    source_id: Mapped[str] = mapped_column(String(100))

    # 名称
    name: Mapped[str] = mapped_column(String(255))

    # 描述
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # 订阅规则（JSON）
    rules: Mapped[dict] = mapped_column(JSON, nullable=True)
    # {
    #   "quality": "flac",  # flac, 320k, standard
    #   "sites": [1, 2, 3],  # 站点ID列表
    #   "min_size": 100 * 1024 * 1024,  # 最小大小（字节）
    #   "max_size": 1024 * 1024 * 1024,  # 最大大小
    #   "free_only": False,  # 只要免费资源
    # }

    # 下载器配置
    downloader: Mapped[str] = mapped_column(String(50), default="qbittorrent")
    save_path: Mapped[str] = mapped_column(String(500), nullable=True)

    # 是否启用
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # 最后检查时间
    last_check: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # 最后发现新内容时间
    last_release: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # 发现的内容数量
    release_count: Mapped[int] = mapped_column(Integer, default=0)
```

### 5.2 PT站点模型（已有，需确认）

与 MoviePilot 类似，站点模型包含：
- 基本信息（名称、域名、URL）
- 认证信息（Cookie、Passkey、用户名、密码）
- 连接配置（代理、UA、超时）
- RSS 配置
- 下载器配置

### 5.3 下载历史模型（更新）

```python
class DownloadHistory(Base, TimestampMixin):
    """下载历史模型"""
    __tablename__ = "download_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 来源
    source: Mapped[str] = mapped_column(String(50))  # subscribe, manual

    # 种子信息
    source_id: Mapped[str] = mapped_column(String(100))  # 种子标题或URL
    torrent_id: Mapped[str] = mapped_column(String(100))  # 种子hash

    # 站点信息
    site: Mapped[str] = mapped_column(String(100))

    # 音乐信息
    title: Mapped[str] = mapped_column(String(255))
    artist: Mapped[str] = mapped_column(String(255), nullable=True)
    album: Mapped[str] = mapped_column(String(255), nullable=True)

    # 种子信息
    size: Mapped[int] = mapped_column(BigInteger)  # 字节
    quality: Mapped[str] = mapped_column(String(50), nullable=True)

    # 下载器信息
    downloader: Mapped[str] = mapped_column(String(50))  # qbittorrent, transmission
    task_id: Mapped[str] = mapped_column(String(100))  # 下载器任务ID

    # 下载状态
    status: Mapped[str] = mapped_column(String(50))  # downloading, completed, failed

    # 进度信息
    progress: Mapped[float] = mapped_column(Float, default=0)
    download_speed: Mapped[int] = mapped_column(BigInteger, nullable=True)  # bytes/s
    eta: Mapped[int] = mapped_column(Integer, nullable=True)  # seconds

    # 文件路径
    file_path: Mapped[str] = mapped_column(String(1000), nullable=True)

    # 错误信息
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    # 完成时间
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
```

---

## 6. 定时任务设计

### 6.1 订阅刷新任务

```python
async def refresh_subsources():
    """订阅源刷新定时任务

    频率：每小时一次
    """
    subscribe_chain = get_chain("subscribe")
    await subscribe_chain.refresh_all()
```

### 6.2 下载进度监控任务

```python
async def monitor_downloads():
    """下载进度监控定时任务

    频率：每分钟一次
    """
    downloader_chain = get_chain("downloader")

    # 检查所有下载器
    for downloader in ["qbittorrent", "transmission"]:
        await downloader_chain.check_completed(downloader)
```

---

## 7. 前端设计（更新）

### 7.1 订阅源管理页面

```
┌─────────────────────────────────────────────────────────────┐
│ 订阅源管理                            [添加订阅源] [刷新全部]  │
├─────────────────────────────────────────────────────────────┤
│ ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐       │
│ │名称  │类型  │状态  │规则  │最后检查│发现│操作 │      │
│ ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤       │
│ │周杰伦│网云│ ✅  │FLAC │10分钟前│23  │编辑 │      │
│ │精选  │歌单 │     │站点 │        │    │删除 │      │
│ ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤       │
│ │热歌   │QQ  │ ✅  │320k │5分钟前 │15  │编辑 │      │
│ │榜     │榜单 │     │无限制│        │    │删除 │      │
│ └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘       │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 PT站点管理页面

```
┌─────────────────────────────────────────────────────────────┐
│ PT站点管理                                 [添加站点] [测试] │
├─────────────────────────────────────────────────────────────┤
│ ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐       │
│ │名称  │站点 │状态 │RSS  │下载器│优先级│操作 │      │
│ ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤       │
│ │M-Team│music│ ✅  │ ✅  │qB    │1     │编辑 │      │
│ │      │.team│     │     │      │     │删除 │      │
│ ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤       │
│ │HDC   │hdc. │ ✅  │ ❌  │qB    │2     │编辑 │      │
│ │      │tl    │     │     │      │     │删除 │      │
│ └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘       │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 下载管理页面

```
┌─────────────────────────────────────────────────────────────┐
│ 下载管理                              [下载中] [已完成] [历史]│
├─────────────────────────────────────────────────────────────┤
│ ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐       │
│ │标题  │大小 │进度 │速度 │ETA  │下载器│操作 │      │
│ ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤       │
│ │周杰伦│1.2GB│███  │5MB/s │3分钟│qB    │暂停 │      │
│ │FLAC  │     │65%  │      │     │      │删除 │      │
│ ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤       │
│ │...   │...  │...  │...  │...  │...  │...  │      │
│ └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. 与之前设计的差异

### 之前的设计（错误）：
- ❌ 直接从网易云音乐/QQ音乐下载音乐文件
- ❌ MusicPilot 自己实现下载功能

### 重新设计（正确）：
- ✅ 从网易云音乐/QQ音乐**抓取歌单/榜单信息**
- ✅ 从**PT站点搜索种子文件**
- ✅ 推送种子到 **qBittorrent/Transmission 下载器**
- ✅ 从下载器**获取下载进度**
- ✅ 下载完成后**整理和元数据补全**

---

## 9. 实现计划

### 需要重新实现的模块：

1. **M4: 下载功能（重新设计）**
   - M4-T1: 下载器对接模块（qBittorrent/Transmission）
   - M4-T2: PT站点搜索模块
   - M4-T3: SubscribeChain 订阅链（重新设计）
   - M4-T4: TorrentsChain 资源链（重新设计）
   - M4-T5: DownloaderChain 下载器链（新增）
   - M4-T6: 订阅源管理界面
   - M4-T7: 下载进度监控界面

2. **M5: 订阅功能（重新设计）**
   - M5-T1: 订阅源抓取模块（网易云音乐/QQ音乐）
   - M5-T2: 订阅源数据模型（更新）
   - M5-T3: 订阅定时任务
   - M5-T4: 订阅规则匹配

---

## 10. 参考资料

- MoviePilot Wiki - 订阅: https://wiki.movie-pilot.org/subscribe
- MoviePilot Wiki - 站点: https://wiki.movie-pilot.org/site
- qBittorrent Web API: https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1+)
- Transmission RPC: https://transmission-rpc.readthedocs.io/