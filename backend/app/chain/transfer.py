"""
转移链
处理下载后文件整理
"""
from typing import Optional
from pathlib import Path

from app.chain import ChainBase
from app.core.context import DownloadTask, MusicInfo
from app.core.log import logger


class TransferChain(ChainBase):
    """
    转移链
    负责按规则整理下载的文件、补全元数据
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.core.config import settings
        self.media_dir = settings.media_path

    async def organize(self, task: DownloadTask) -> Optional[MusicInfo]:
        """
        整理下载的文件

        Args:
            task: 下载任务对象

        Returns:
            整理后的音乐信息对象
        """
        self.logger.info(f"整理文件: {task.source.title}")

        # 检查文件是否存在
        source_path = Path(task.file_path)
        if not source_path.exists():
            self.logger.error(f"源文件不存在: {source_path}")
            return None

        # 生成目标路径
        target_path = await self.generate_path(task)

        # 移动文件
        target_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.rename(target_path)

        # 更新任务中的文件路径
        task.file_path = str(target_path)

        self.logger.info(f"文件已移动到: {target_path}")

        # 返回基本信息，元数据补全由 MetadataChain 处理
        return MusicInfo(
            artist=task.source.artist,
            album=task.source.album,
            title=task.source.title,
            path=str(target_path),
        )

    async def generate_path(self, task: DownloadTask) -> Path:
        """
        生成目标文件路径

        Args:
            task: 下载任务对象

        Returns:
            目标文件路径
        """
        # 按规则生成路径: Artist/Album/Track.mp3
        artist = task.source.artist or "Unknown Artist"
        album = task.source.album or "Unknown Album"
        title = task.source.title or "Unknown Track"

        # 清理文件名
        safe_artist = self._sanitize_filename(artist)
        safe_album = self._sanitize_filename(album)
        safe_title = self._sanitize_filename(title)

        # 获取文件扩展名
        source_ext = Path(task.file_path).suffix

        # 生成完整路径
        target_path = self.media_dir / safe_artist / safe_album / f"{safe_title}{source_ext}"

        return target_path

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
        safe = re.sub(r'[<>:"/\\|?*]', '', filename)
        # 替换多个空格为单个空格
        safe = re.sub(r'\s+', ' ', safe).strip()
        return safe or "Unknown"