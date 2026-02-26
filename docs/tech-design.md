# MusicPilot - 技术设计文档 v3.0

> **版本**: v3.0
> **基于**: 需求分析文档 v2.0（含资源站点功能）+ MoviePilot 架构研究
> **最后更新**: 2026-02-26

---

## 1. 架构概述

### 1.1 设计原则

参考 MoviePilot v2 架构，采用 **Chain + Module + Plugin 三层架构**，针对音乐资源管理领域进行适配：

1. **核心原则**
   - **Chain 层**: 业务逻辑编排，协调模块和插件
   - **Module 层**: 独立功能模块（资源站点、元数据、下载器、媒体服务器）
   - **Plugin 层**: 用户扩展，支持劫持系统模块
   - **事件驱动**: 松耦合模块间通信
   - **配置驱动**: 通过配置文件控制行为

2. **音乐资源管理适配**
   - **元数据源**: MusicBrainz（替代 TMDB）
   - **媒体类型**: Artist、Album、Track（替代 Movie、TV、Episode）
   - **播放功能**: 音频流、播放列表
   - **订阅类型**: 艺术家/专辑订阅
   - **资源站点**: 支持多个音乐 资源站点
   - **下载方式**: 种子文件 + 下载器（qBittorrent/Transmission）

---

## 2. Chain 层设计（更新）

### 2.1 TorrentsChain（资源链）【新增】

**职责**: 管理 资源站点，搜索音乐资源，下载种子文件

```python
class TorrentsChain(ChainBase):
    """资源链"""

    def search(self, keyword: str, sites: List[int] = None, 
                category: str = None, filters: dict = None) -> List[TorrentInfo]:
        """在资源站点搜索音乐资源
        
        Args:
            keyword: 搜索关键词（艺术家/专辑/曲目）
            sites: 站点 ID 列表，为空则搜索所有启用站点
            category: 分类（music/flac/mp3/lossless）
            filters: 高级过滤条件（大小、编码、免费状态等）
        
        Returns:
            TorrentInfo 列表
        """
        results = []
        
        # 获取要搜索的站点
        if sites:
            site_list = [self.get_site(site_id) for site_id in sites]
        else:
            site_list = self.run_module("get_active_sites")
        
        # 并发搜索
        for site in site_list:
            try:
                site_results = self.run_module(
                    "search_torrents",
                    site=site,
                    keyword=keyword,
                    category=category,
                    filters=filters
                )
                results.extend(site_results)
            except Exception as e:
                logger.error(f"站点 {site.name} 搜索失败：{e}")
        
        # 去重和排序
        results = self.deduplicate_and_sort(results)
        
        return results

    def download_torrent(self, torrent: TorrentInfo) -> str:
        """下载种子文件
        
        Args:
            torrent: TorrentInfo 对象
        
        Returns:
            种子文件路径
        """
        # 从站点下载种子
        site = self.get_site(torrent.site)
        torrent_file = self.run_module("download_torrent", site, torrent)
        
        # 保存种子文件
        torrent_path = self.save_torrent(torrent_file, torrent)
        
        # 发送事件
        self.send_event(EventType.TorrentDownloaded, {
            "torrent": torrent,
            "path": torrent_path
        })
        
        return torrent_path

    def push_to_downloader(self, torrent: TorrentInfo, downloader: str) -> DownloadTask:
        """推送到下载器
        
        Args:
            torrent: TorrentInfo 对象
            downloader: 下载器类型（qbittorrent/transmission）
        
        Returns:
            DownloadTask 对象
        """
        # 创建下载任务
        task = DownloadTask(
            torrent_id=torrent.site,
            torrent_name=torrent.title,
            torrent_url=torrent.enclosure,
            downloader=downloader,
            status="downloading"
        )
        
        # 推送到下载器
        if downloader == "qbittorrent":
            self.run_module("push_to_qbittorrent", task)
        elif downloader == "transmission":
            self.run_module("push_to_transmission", task)
        
        # 发送事件
        self.send_event(EventType.DownloadStarted, {
            "task": task
        })
        
        return task

    def browse_site(self, domain: str, page: int = 0, 
                     category: str = None) -> List[TorrentInfo]:
        """浏览站点首页
        
        Args:
            domain: 站点域名
            page: 页码
            category: 分类
        
        Returns:
            TorrentInfo 列表
        """
        site = self.get_site_by_domain(domain)
        if not site:
            return []
        
        results = self.run_module(
            "browse_site",
            site=site,
            page=page,
            category=category
        )
        
        return results

    def get_site_rss(self, domain: str) -> List[TorrentInfo]:
        """获取站点 RSS
        
        Args:
            domain: 站点域名
        
        Returns:
            TorrentInfo 列表
        """
        site = self.get_site_by_domain(domain)
        if not site or not site.rss:
            return []
        
        # 解析 RSS
        rss_items = self.run_module(
            "parse_rss",
            url=site.rss,
            use_proxy=site.proxy,
            timeout=site.timeout,
            ua=site.ua
        )
        
        # 组装 TorrentInfo
        results = []
        for item in rss_items:
            torrent_info = TorrentInfo(
                site=site.id,
                site_name=site.name,
                site_cookie=site.cookie,
                site_ua=site.ua,
                site_proxy=site.proxy,
                site_order=site.pri,
                site_downloader=site.downloader,
                title=item.title,
                enclosure=item.enclosure,
                page_url=item.link,
                size=item.size,
                pubdate=item.pubdate,
            )
            results.append(torrent_info)
        
        return results
```

---

## 3. Module 层设计（更新）

### 3.1 SiteModule（站点模块）【新增】

```python
class SiteModule:
    """站点模块"""

    @classmethod
    def init_setting(cls):
        return ("SITE_ENABLE", True)

    def __init__(self):
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )

    def login(self, site: Site):
        """登录站点"""
        if site.cookie:
            # 设置 Cookie
            self.set_cookie(site.cookie)
            return True
        
        # 如果没有 Cookie，尝试 Passkey 登录
        if site.passkey:
            return self.login_with_passkey(site.passkey)
        
        return False

    def search_torrents(self, site: Site, keyword: str, 
                        category: str = None, filters: dict = None) -> List[TorrentInfo]:
        """搜索种子
        
        Args:
            site: 站点配置
            keyword: 搜索关键词
            category: 分类
            filters: 过滤条件
        
        Returns:
            TorrentInfo 列表
        """
        # 构建搜索 URL
        search_url = self.build_search_url(site, keyword, category, filters)
        
        # 发送请求
        response = self.request(search_url, site)
        
        # 解析搜索结果
        results = self.parse_search_results(response, site)
        
        return results

    def download_torrent(self, site: Site, torrent: TorrentInfo) -> bytes:
        """下载种子文件
        
        Args:
            site: 站点配置
            torrent: TorrentInfo 对象
        
        Returns:
            种子文件内容
        """
        response = self.request(torrent.enclosure, site)
        return response.content

    def browse_site(self, site: Site, page: int = 0, 
                    category: str = None) -> List[TorrentInfo]:
        """浏览站点首页"""
        browse_url = self.build_browse_url(site, page, category)
        response = self.request(browse_url, site)
        results = self.parse_browse_results(response, site)
        return results

    def request(self, url: str, site: Site):
        """发送 HTTP 请求"""
        if site.proxy:
            # 使用代理
            proxy_handler = urllib.request.ProxyHandler({'http': site.proxy, 'https': site.proxy})
            opener = urllib.request.build_opener(proxy_handler)
        else:
            opener = self.opener
        
        # 设置 User-Agent
        headers = {'User-Agent': site.ua or settings.USER_AGENT}
        
        request = urllib.request.Request(url, headers=headers)
        
        try:
            response = opener.open(request, timeout=site.timeout or 15)
            return response
        except Exception as e:
            logger.error(f"请求 {url} 失败：{e}")
            raise
```

### 3.2 AdapterModule（适配器模块）【新增】

支持不同的资源站点，每个站点有自己的适配器。用户可以通过插件系统扩展自定义站点适配器。

```python
# SiteAdapterModule - 适配器基类
class SiteAdapter(SiteModule):
    """资源站点适配器"""
    pass

# 用户可以通过插件系统扩展自定义站点适配器
```

---

## 4. 数据库设计（更新）

### 4.1 Site（资源站点表）【新增】

```python
class Site(Base):
    """资源站点表"""
    __tablename__ = "site"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # 站点名称
    name = Column(String(100), nullable=False)
    # 域名 Key
    domain = Column(String(255), unique=True, index=True, nullable=False)
    # 站点地址
    url = Column(String(500), nullable=False)
    # 站点优先级（1-10，数字越大优先级越高）
    pri = Column(Integer, default=1, index=True)
    # RSS 地址
    rss = Column(String(500))
    # Cookie
    cookie = Column(Text)
    # Passkey
    passkey = Column(String(100))
    # User-Agent
    ua = Column(String(500))
    # 是否使用代理（0-否，1-是）
    proxy = Column(Integer, default=0)
    # 过滤规则
    filter = Column(Text)
    # 是否渲染（是否启用搜索）
    render = Column(Integer, default=1)
    # 是否公开站点
    public = Column(Integer, default=0)
    # 附加信息
    note = Column(JSON)
    # 流控单位周期
    limit_interval = Column(Integer, default=0)
    # 流控次数
    limit_count = Column(Integer, default=0)
    # 流控间隔（秒）
    limit_seconds = Column(Integer, default=0)
    # 超时时间（秒）
    timeout = Column(Integer, default=15)
    # 是否启用
    is_active = Column(Boolean, default=True)
    # 关联下载器（qbittorrent/transmission）
    downloader = Column(String(50))
    # 最后修改时间
    lst_mod_date = Column(String, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    # 创建时间
    created_at = Column(DateTime, default=datetime.now)
    # 更新时间
    updated_at = Column(DateTime, onupdate=datetime.now)
```

### 4.2 TorrentInfo（种子信息）【新增】

```python
class TorrentInfo(BaseModel):
    """种子信息"""
    
    # 站点信息
    site: int = None                # 站点 ID
    site_name: str = None           # 站点名称
    site_cookie: str = None        # 站点 Cookie
    site_ua: str = None            # 站点 User-Agent
    site_proxy: bool = False       # 是否使用代理
    site_order: int = 0           # 站点优先级
    site_downloader: str = None    # 关联下载器
    
    # 种子信息
    title: str = None              # 种子标题
    description: str = None       # 副标题
    enclosure: str = None          # 下载链接
    page_url: str = None           # 详情页面
    size: float = 0.0             # 文件大小（字节）
    seeders: int = 0              # 做种数
    leechers: int = 0             # 下载数
    grabs: int = 0                 # 完成数
    pubdate: str = None           # 发布时间
    date_elapsed: str = None       # 已发布时间
    
    # 促销信息
    upload_factor: float = None   # 上传倍率
    download_factor: float = None  # 下载倍率
    hit_and_run: bool = False      # HR 状态
    
    # 分类
    category: str = None          # 分类
    
    # 其他
    labels: List[str] = []         # 标签
    pri_order: int = 0             # 种子优先级
```

---

## 5. API 设计（更新）

### 5.1 Site API（新增）

| 方法 | 路径 | 描述 | 参数 |
|------|------|------|------|
| GET | `/sites` | 列出 资源站点 | - |
| POST | `/sites` | 添加 资源站点 | name, domain, url, cookie, passkey, ua, proxy, downloader, pri |
| GET | `/sites/{id}` | 获取站点详情 | - |
| PUT | `/sites/{id}` | 更新站点 | - |
| DELETE | `/sites/{id}` | 删除站点 | - |
| POST | `/sites/{id}/test` | 测试站点连接 | - |
| PUT | `/sites/{id}/enable` | 启用站点 | - |
| PUT | `/sites/{id}/disable` | 禁用站点 | - |

### 5.2 Search API（更新）

| 方法 | 路径 | 描述 | 参数 |
|------|------|------|------|
| GET | `/search/torrents` | 搜索资源 | keyword, sites, category, filters |
| GET | `/sites/{domain}/browse` | 浏览站点首页 | page, category |
| GET | `/sites/{domain}/rss` | 获取站点 RSS | - |

### 5.3 Download API（更新）

| 方法 | 路径 | 描述 | 参数 |
|------|------|------|------|
| POST | `/download/torrent` | 下载种子文件 | torrent_id |
| POST | `/download/push` | 推送到下载器 | torrent_id, downloader |
| GET | `/download/history` | 下载历史 | page, page_size, status |

---

## 6. 前端设计（更新）

### 6.1 页面结构（新增）

```
src/
├── views/
│   ├── site/
│   │   ├── SiteListView.vue       # 资源站点列表
│   │   └── SiteDetailView.vue     # 站点详情
│   ├── search/
│   │   └── SearchView.vue         # 资源搜索
│   └── download/
│       └── DownloadView.vue       # 下载管理
```

### 6.2 资源站点管理组件

```vue
<!-- SiteListView.vue -->
<template>
  <div class="site-list">
    <n-button type="primary" @click="showAddSiteModal">添加站点</n-button>
    <n-data-table
      :columns="columns"
      :data="sites"
      :pagination="pagination"
    />
    <n-modal v-model:show="showAddModal">
      <n-form :model="newSite" label-placement="left">
        <n-form-item label="站点名称">
          <n-input v-model:value="newSite.name" placeholder="自定义站点名称" />
        </n-form-item>
        <n-form-item label="站点地址">
          <n-input v-model:value="newSite.url" placeholder="https://example.com" />
        </n-form-item>
        <n-form-item label="Cookie">
          <n-input type="textarea" v-model:value="newSite.cookie" placeholder="ccc_xxx=..." />
        </n-form-item>
        <n-form-item label="下载器">
          <n-select v-model:value="newSite.downloader">
            <n-option value="qbittorrent">qBittorrent</n-option>
            <n-option value="transmission">Transmission</n-option>
          </n-select>
        </n-form-item>
        <n-form-item>
          <n-button type="primary" @click="addSite">添加</n-button>
        </n-form-item>
      </n-form>
    </n-modal>
  </div>
</template>
```

---

## 7. 开发任务拆解（更新）

### 7.1 M4: 资源站点和下载功能（更新）

**目标**: 实现 资源站点管理和音乐资源下载

**任务列表**:

| 任务 | 描述 | 预计工时 |
|------|------|----------|
| M4-T1 | 资源站点数据模型 | 4h |
| M4-T2 | TorrentsChain 实现 | 10h |
| M4-T3 | 站点模块 | 12h |
| M4-T4 | 适配器 | 8h |
| M4-T5 | 搜索 API | 6h |
| M4-T6 | 下载 API | 6h |
| M4-T7 | 前端站点管理界面 | 8h |
| M4-T8 | 前端搜索界面 | 6h |
| M4-T9 | 前端下载管理界面 | 6h |

---

## 8. 参考资料

- MoviePilot: https://github.com/jxxghp/MoviePilot
- MoviePilot Wiki: https://wiki.movie-pilot.org
- MusicBrainz API: https://musicbrainz.org/doc/MusicBrainz_API
- FastAPI: https://fastapi.tiangolo.com/
- Vue 3: https://vuejs.org/