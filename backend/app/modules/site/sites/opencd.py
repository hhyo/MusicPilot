"""OpenCD 站点实现"""

import httpx
from bs4 import BeautifulSoup

from ..models import SiteConfig, TorrentInfo


class OpenCDSite:
    """OpenCD 站点"""

    def __init__(self, config: SiteConfig):
        self.config = config
        self.name = config.name
        self.base_url = config.url
        self.cookie = config.cookie

    async def search(self, keyword: str) -> list[TorrentInfo]:
        """搜索种子"""
        url = f"{self.base_url}/torrents.php"
        params = {"search": keyword}
        headers = {"Cookie": self.cookie} if self.cookie else {}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)

        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        torrents = []

        table = soup.find("table", class_="torrents")
        if not table:
            return []

        # Find all rows - handle both with and without header
        rows = table.find_all("tr")
        data_rows = rows if len(rows) <= 1 else rows[1:]

        for row in data_rows:
            cells = row.find_all("td")
            if len(cells) < 3:
                continue

            name_cell = cells[0].find("a")
            if not name_cell:
                continue

            name = name_cell.get_text(strip=True)
            href = name_cell.get("href", "")

            # Extract ID from href like /details.php?id=12345
            torrent_id = ""
            if "id=" in href:
                torrent_id = href.split("id=")[1].split("&")[0]

            # Parse size, seeders, leechers
            size_cell = cells[1].get_text(strip=True) if len(cells) > 1 else "0"
            seeders_cell = cells[2].get_text(strip=True) if len(cells) > 2 else "0"
            leechers_cell = cells[3].get_text(strip=True) if len(cells) > 3 else "0"

            # Convert size to bytes (simplified)
            size = self._parse_size(size_cell)

            torrents.append(TorrentInfo(
                id=torrent_id,
                name=name,
                site=self.name,
                size=size,
                seeders=int(seeders_cell) if seeders_cell.isdigit() else 0,
                leechers=int(leechers_cell) if leechers_cell.isdigit() else 0,
                download_url=f"{self.base_url}/download.php?id={torrent_id}"
            ))

        return torrents

    async def get_download_url(self, torrent_id: str) -> str:
        """获取下载链接"""
        return f"{self.base_url}/download.php?id={torrent_id}"

    def _parse_size(self, size_str: str) -> int:
        """解析大小字符串为字节"""
        size_str = size_str.upper().strip()
        multipliers = {
            "B": 1,
            "KB": 1024,
            "MB": 1024**2,
            "GB": 1024**3,
            "TB": 1024**4
        }

        for unit, mult in multipliers.items():
            if unit in size_str:
                try:
                    num = float(size_str.replace(unit, "").strip())
                    return int(num * mult)
                except ValueError:
                    return 0

        try:
            return int(size_str)
        except ValueError:
            return 0
