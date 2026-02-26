"""
订阅链
处理艺术家/专辑订阅
"""
from typing import List, Dict, Any

from app.chain import ChainBase
from app.core.log import logger


class SubscribeChain(ChainBase):
    """
    订阅链
    负责检查订阅更新、发现新内容、下载新内容
    """

    async def check(self, subscribe_type: str, musicbrainz_id: str) -> Dict[str, Any]:
        """
        检查订阅更新

        Args:
            subscribe_type: 订阅类型（artist, album）
            musicbrainz_id: MusicBrainz ID

        Returns:
            检查结果字典
        """
        self.logger.info(f"检查订阅更新: {subscribe_type} - {musicbrainz_id}")

        # 调用 MusicBrainz 模块查询
        if subscribe_type == "artist":
            info = await self.run_module("musicbrainz", "get_artist_info", musicbrainz_id)
            # 查找新专辑
            releases = info.get("releases", [])
        else:  # album
            info = await self.run_module("musicbrainz", "get_album_info", musicbrainz_id)
            releases = [info] if info else []

        result = {
            "has_new": len(releases) > 0,
            "releases": releases,
            "last_check": info.get("last_updated"),
        }

        # 发送订阅检查事件
        self.send_event("subscribe.checked", {
            "type": subscribe_type,
            "musicbrainz_id": musicbrainz_id,
            "has_new": result["has_new"],
        })

        return result

    async def discover(self, subscribe_type: str, musicbrainz_id: str) -> List[Dict[str, Any]]:
        """
        发现新内容

        Args:
            subscribe_type: 订阅类型
            musicbrainz_id: MusicBrainz ID

        Returns:
            新内容列表
        """
        self.logger.info(f"发现新内容: {subscribe_type} - {musicbrainz_id}")

        # 检查更新
        result = await self.check(subscribe_type, musicbrainz_id)

        if not result["has_new"]:
            self.logger.info(f"没有新内容: {subscribe_type} - {musicbrainz_id}")
            return []

        # 返回新内容
        new_releases = result["releases"]

        # 发送新内容发现事件
        self.send_event("subscribe.new_release", {
            "type": subscribe_type,
            "musicbrainz_id": musicbrainz_id,
            "releases": new_releases,
        })

        return new_releases

    async def download(self, releases: List[Dict[str, Any]], format: str = "mp3") -> List[Dict[str, Any]]:
        """
        下载新内容

        Args:
            releases: 发布内容列表
            format: 下载格式

        Returns:
            下载任务列表
        """
        self.logger.info(f"开始下载新内容，共 {len(releases)} 个")

        from app.chain.download import DownloadChain
        download_chain = DownloadChain(
            event_manager=self.event_manager,
            module_manager=self.module_manager,
            plugin_manager=self.plugin_manager,
            cache=self.cache,
        )

        download_tasks = []

        for release in releases:
            # 搜索专辑
            query = f"{release.get('artist')} {release.get('title')}"
            sources = await download_chain.search(query)

            if sources:
                # 使用第一个源下载
                task = await download_chain.download(sources[0], "")
                download_tasks.append({
                    "release": release,
                    "task": task,
                })

        # 发送订阅完成事件
        self.send_event("subscribe.complete", {
            "total": len(releases),
            "downloaded": len(download_tasks),
        })

        return download_tasks

    async def record_history(self, subscribe_type: str, musicbrainz_id: str, releases: List[Dict[str, Any]]):
        """
        记录订阅历史

        Args:
            subscribe_type: 订阅类型
            musicbrainz_id: MusicBrainz ID
            releases: 发布内容列表
        """
        self.logger.info(f"记录订阅历史: {subscribe_type} - {musicbrainz_id}")

        # TODO: 实现订阅历史记录到数据库
        # 这里需要创建 SubscribeHistory 模型和 Oper

        pass