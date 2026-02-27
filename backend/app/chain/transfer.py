"""
转移链
处理下载后文件整理
"""

from hashlib import md5
from pathlib import Path

from app.chain import ChainBase
from app.core.context import DownloadTask, MusicInfo
from app.core.event import EventType
from app.core.log import logger
from app.db.operations.track import TrackOper


class TransferChain(ChainBase):
    """
    转移链
    负责按规则整理下载的文件、补全元数据
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.core.config import settings

        self.media_dir = Path(settings.media_path)
        self.logger = logger
        self.track_oper = TrackOper(self.db_manager)

    async def organize(
        self, task: DownloadTask, check_duplicate: bool = True
    ) -> MusicInfo | None:
        """
        整理下载的文件

        Args:
            task: 下载任务对象
            check_duplicate: 是否检查重复

        Returns:
            整理后的音乐信息对象
        """
        self.logger.info(f"整理文件: {task.title or task.task_id}")

        # 检查文件是否存在
        source_path = Path(task.file_path)
        if not source_path.exists():
            self.logger.error(f"源文件不存在: {source_path}")
            await self._send_transfer_event(task, success=False, error="源文件不存在")
            return None

        # 检查文件去重
        if check_duplicate:
            duplicate = await self._check_duplicate(source_path, task)
            if duplicate:
                self.logger.warning(f"发现重复文件: {source_path}")
                # 删除重复文件
                source_path.unlink()
                await self._send_transfer_event(task, success=False, error="文件重复")
                return None

        # 生成目标路径
        target_path = await self.generate_path(task)

        # 移动文件
        target_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.rename(target_path)

        # 更新任务中的文件路径
        task.file_path = str(target_path)

        self.logger.info(f"文件已移动到: {target_path}")

        # 返回基本信息
        music_info = MusicInfo(
            artist=task.artist,
            album=task.album,
            title=task.title,
            path=str(target_path),
            file_format=target_path.suffix[1:],
            file_size=task.total_bytes,
        )

        # 调用 MetadataChain 补全元数据
        await self._complete_metadata(music_info, task)

        # 通知 MediaServer（可选）
        await self._sync_to_media_server(music_info)

        # 发送转移完成事件
        await self._send_transfer_event(task, success=True)

        return music_info

    async def generate_path(self, task: DownloadTask) -> Path:
        """
        生成目标文件路径

        Args:
            task: 下载任务对象

        Returns:
            目标文件路径
        """
        # 按规则生成路径: Artist/Album/Track.mp3
        artist = task.artist or "Unknown Artist"
        album = task.album or "Unknown Album"
        title = task.title or "Unknown Track"

        # 清理文件名
        safe_artist = self._sanitize_filename(artist)
        safe_album = self._sanitize_filename(album)
        safe_title = self._sanitize_filename(title)

        # 获取文件扩展名
        source_ext = Path(task.file_path).suffix

        # 生成完整路径
        target_path = self.media_dir / safe_artist / safe_album / f"{safe_title}{source_ext}"

        # 如果文件已存在，添加序号
        counter = 1
        while target_path.exists():
            target_path = (
                self.media_dir / safe_artist / safe_album / f"{safe_title}_{counter}{source_ext}"
            )
            counter += 1

        return target_path

    async def _check_duplicate(self, file_path: Path, task: DownloadTask) -> dict | None:
        """
        检查文件是否重复

        Args:
            file_path: 文件路径
            task: 下载任务

        Returns:
            重复文件信息，如果不重复则返回 None
        """
        # 1. 通过 MusicBrainz ID 检查
        musicbrainz_id = task.metadata.get("musicbrainz_id")
        if musicbrainz_id:
            existing_track = await self.track_oper.get_by_musicbrainz_id(musicbrainz_id)
            if existing_track:
                return {
                    "type": "musicbrainz_id",
                    "track_id": existing_track.id,
                    "path": existing_track.path,
                }

        # 2. 通过文件大小和时长检查
        file_size = file_path.stat().st_size
        duration = task.metadata.get("duration")

        existing_tracks = await self.track_oper.get_by_size_and_duration(file_size, duration)
        if existing_tracks:
            return {
                "type": "size_duration",
                "tracks": existing_tracks,
            }

        # 3. 通过文件指纹（MD5）检查
        md5_hash = self._calculate_md5(file_path)
        existing_track = await self.track_oper.get_by_file_hash(md5_hash)
        if existing_track:
            return {
                "type": "file_hash",
                "track_id": existing_track.id,
                "path": existing_track.path,
            }

        return None

    def _calculate_md5(self, file_path: Path) -> str:
        """
        计算文件 MD5 哈希

        Args:
            file_path: 文件路径

        Returns:
            MD5 哈希值
        """
        hash_md5 = md5()
        with open(file_path, "rb") as f:
            # 读取前 1MB 和后 1MB 用于快速计算
            chunk = f.read(1024 * 1024)
            hash_md5.update(chunk)

            # 如果文件小于 2MB，读取整个文件
            if file_path.stat().st_size <= 2 * 1024 * 1024:
                f.seek(0)
                remaining = f.read()
                hash_md5.update(remaining)
            else:
                # 读取最后 1MB
                f.seek(-1024 * 1024, 2)
                chunk = f.read()
                hash_md5.update(chunk)

        return hash_md5.hexdigest()

    async def _complete_metadata(self, music_info: MusicInfo, task: DownloadTask):
        """
        调用 MetadataChain 补全元数据

        Args:
            music_info: 音乐信息
            task: 下载任务
        """
        try:
            # 调用 MetadataChain
            result = await self.run_module(
                "metadata",
                action="complete",
                music_info=music_info,
            )

            if result:
                self.logger.info(f"元数据补全成功: {music_info.title}")
            else:
                self.logger.warning(f"元数据补全失败: {music_info.title}")

        except Exception as e:
            self.logger.error(f"元数据补全异常: {e}")

    async def _sync_to_media_server(self, music_info: MusicInfo):
        """
        同步到媒体服务器

        Args:
            music_info: 音乐信息
        """
        try:
            # 调用 MediaChain 同步
            await self.run_module(
                "media",
                action="scan_library",
                music_info=music_info,
            )
        except Exception as e:
            # 媒体服务器同步失败不影响整理流程
            self.logger.warning(f"媒体服务器同步失败（可忽略）: {e}")

    async def _send_transfer_event(
        self, task: DownloadTask, success: bool, error: str | None = None
    ):
        """
        发送转移事件

        Args:
            task: 下载任务
            success: 是否成功
            error: 错误信息
        """
        event_type = EventType.TRANSFER_COMPLETED if success else EventType.TRANSFER_FAILED

        await self.put_message(
            event_type,
            {
                "task_id": task.task_id,
                "title": task.title,
                "artist": task.artist,
                "album": task.album,
                "file_path": task.file_path,
                "success": success,
                "error": error,
            },
        )

    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除不安全字符

        Args:
            filename: 原始文件名

        Returns:
            清理后的文件名
        """
        import re

        # 移除不安全字符
        safe = re.sub(r'[<>:"/\\|?*]', "", filename)
        # 替换多个空格为单个空格
        safe = re.sub(r"\s+", " ", safe).strip()
        return safe or "Unknown"
