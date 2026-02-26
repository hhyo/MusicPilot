"""
媒体链
处理媒体服务器同步
"""
from typing import List, Dict, Any, Optional

from app.chain import ChainBase
from app.core.log import logger


class MediaChain(ChainBase):
    """
    媒体链
    负责媒体服务器的扫描、元数据同步、播放状态同步
    """

    async def scan_library(self, server_id: int) -> Dict[str, Any]:
        """
        扫描音乐库到媒体服务器

        Args:
            server_id: 媒体服务器 ID

        Returns:
            扫描结果
        """
        self.logger.info(f"扫描音乐库: 媒体服务器 {server_id}")

        # 获取媒体服务器配置
        from app.db.operations.media import MediaServerOper
        media_oper = MediaServerOper(self.db_manager)
        server = await media_oper.get_by_id(server_id)

        if not server:
            self.logger.error(f"媒体服务器不存在: {server_id}")
            return {"success": False, "error": "媒体服务器不存在"}

        # 获取本地曲目
        from app.db.operations.track import TrackOper
        track_oper = TrackOper(self.db_manager)
        tracks = await track_oper.get_all(limit=1000)

        # 调用媒体服务器模块同步
        if server.type == "plex":
            result = await self.run_module("plex", "music_library_scanner", server, tracks)
        elif server.type == "jellyfin":
            result = await self.run_module("jellyfin", "music_library_scanner", server, tracks)
        else:
            self.logger.warning(f"不支持的媒体服务器类型: {server.type}")
            return {"success": False, "error": f"不支持的类型: {server.type}"}

        # 发送扫描完成事件
        self.send_event("media.sync_completed", {
            "server_id": server_id,
            "server_type": server.type,
            "track_count": len(tracks),
        })

        return result

    async def sync_metadata(self, server_id: int) -> Dict[str, Any]:
        """
        同步元数据到媒体服务器

        Args:
            server_id: 媒体服务器 ID

        Returns:
            同步结果
        """
        self.logger.info(f"同步元数据: 媒体服务器 {server_id}")

        # 获取媒体服务器配置
        from app.db.operations.media import MediaServerOper
        media_oper = MediaServerOper(self.db_manager)
        server = await media_oper.get_by_id(server_id)

        if not server:
            return {"success": False, "error": "媒体服务器不存在"}

        # 获取需要同步的曲目
        from app.db.operations.track import TrackOper
        track_oper = TrackOper(self.db_manager)
        tracks = await track_oper.get_all(limit=1000)

        # 调用媒体服务器模块同步
        if server.type == "plex":
            result = await self.run_module("plex", "update_track_metadata", server, tracks)
        elif server.type == "jellyfin":
            result = await self.run_module("jellyfin", "update_track_metadata", server, tracks)
        else:
            return {"success": False, "error": f"不支持的类型: {server.type}"}

        return result

    async def sync_playback(self, session_data: Dict[str, Any]):
        """
        同步播放状态到媒体服务器

        Args:
            session_data: 播放会话数据
        """
        self.logger.info(f"同步播放状态: {session_data.get('track_id')}")

        # 获取启用的媒体服务器
        from app.db.operations.media import MediaServerOper
        media_oper = MediaServerOper(self.db_manager)
        servers = await media_oper.get_enabled()

        # 同步到所有启用的服务器
        for server in servers:
            if server.type == "plex":
                await self.run_module("plex", "sync_playback", server, session_data)
            elif server.type == "jellyfin":
                await self.run_module("jellyfin", "sync_playback", server, session_data)

    async def sync_stop(self, session_data: Dict[str, Any]):
        """
        同步停止状态到媒体服务器

        Args:
            session_data: 播放会话数据
        """
        self.logger.info(f"同步停止状态: {session_data.get('track_id')}")

        # 获取启用的媒体服务器
        from app.db.operations.media import MediaServerOper
        media_oper = MediaServerOper(self.db_manager)
        servers = await media_oper.get_enabled()

        # 同步到所有启用的服务器
        for server in servers:
            if server.type == "plex":
                await self.run_module("plex", "sync_stop", server, session_data)
            elif server.type == "jellyfin":
                await self.run_module("jellyfin", "sync_stop", server, session_data)

    async def get_status(self, server_id: int) -> Dict[str, Any]:
        """
        获取媒体服务器状态

        Args:
            server_id: 媒体服务器 ID

        Returns:
            服务器状态
        """
        self.logger.info(f"获取媒体服务器状态: {server_id}")

        # 获取媒体服务器配置
        from app.db.operations.media import MediaServerOper
        media_oper = MediaServerOper(self.db_manager)
        server = await media_oper.get_by_id(server_id)

        if not server:
            return {"success": False, "error": "媒体服务器不存在"}

        # 测试连接
        success, message = await media_oper.test_connection(server_id)

        return {
            "connected": success,
            "message": message,
            "type": server.type,
            "name": server.name,
            "host": server.host,
        }