"""MTeam 站点实现"""

import httpx

from ..models import SiteConfig, TorrentDetail, TorrentInfo


class MTeamSite:
    """MTeam 站点"""

    def __init__(self, config: SiteConfig):
        self.config = config
        self.name = config.name
        self.base_url = config.url
        self.api_key = config.api_key

    async def search(self, keyword: str) -> list[TorrentInfo]:
        """搜索种子"""
        url = f"{self.base_url}/api/torrent/search"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = {"keyword": keyword}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)

        if response.status_code != 200:
            return []

        result = response.json()
        torrents = []

        for item in result.get("data", []):
            torrents.append(TorrentInfo(
                id=item.get("id"),
                name=item.get("name"),
                site=self.name,
                size=int(item.get("size", 0)),
                seeders=item.get("seeders", 0),
                leechers=item.get("leechers", 0),
                download_url=item.get("downloadUrl", "")
            ))

        return torrents

    async def get_detail(self, torrent_id: str) -> TorrentDetail:
        """获取种子详情"""
        url = f"{self.base_url}/api/torrent/{torrent_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)

        if response.status_code != 200:
            return None

        data = response.json().get("data", {})

        return TorrentDetail(
            id=data.get("id"),
            name=data.get("name"),
            size=int(data.get("size", 0)),
            description=data.get("description", ""),
            files=data.get("files", []),
            seeders=data.get("seeders", 0),
            leechers=data.get("leechers", 0)
        )
