"""
元数据处理链
处理音乐元数据的识别、补全
"""

from typing import Optional, Dict, Any, List
from pathlib import Path

from app.chain import ChainBase
from app.core.context import MusicInfo
from app.core.meta import MetadataParser, FilenameParser
from app.core.log import logger
from app.db.operations.artist import ArtistOper
from app.db.operations.album import AlbumOper
from app.db.operations.track import TrackOper
from app.db import db_manager


class MetadataChain(ChainBase):
    """
    元数据处理链
    负责提取本地元数据、解析文件名、查询在线数据库、补全元数据
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metadata_parser = MetadataParser()
        self.filename_parser = FilenameParser()

    async def recognize(self, file_path: str) -> Optional[MusicInfo]:
        """
        识别音乐文件的元数据

        Args:
            file_path: 文件路径

        Returns:
            音乐信息对象
        """
        path = Path(file_path)

        # 1. 提取本地元数据
        local_metadata = self.metadata_parser.parse_file(path)

        # 2. 解析文件名
        filename_metadata = self.filename_parser.parse(path)

        # 3. 合并元数据（文件名优先级较低）
        if local_metadata:
            merged = MusicInfo(
                artist=local_metadata.artist or filename_metadata.artist,
                album=local_metadata.album or filename_metadata.album,
                title=local_metadata.title or filename_metadata.title,
                duration=local_metadata.duration or filename_metadata.duration,
                track_number=local_metadata.track_number or filename_metadata.track_number,
                disc_number=local_metadata.disc_number,
                path=str(path),
                file_format=local_metadata.file_format,
                file_size=local_metadata.file_size,
                bitrate=local_metadata.bitrate,
                sample_rate=local_metadata.sample_rate,
                channels=local_metadata.channels,
                genres=local_metadata.genres or filename_metadata.genres,
                musicbrainz_artist_id=local_metadata.musicbrainz_artist_id,
                musicbrainz_album_id=local_metadata.musicbrainz_album_id,
                musicbrainz_track_id=local_metadata.musicbrainz_track_id,
            )
        else:
            merged = filename_metadata
            merged.path = str(path)

        self.logger.info(f"识别元数据: {path.name}")

        return merged

    async def extract_local_metadata(self, file_path: Path) -> MusicInfo:
        """提取本地元数据"""
        return self.metadata_parser.parse_file(file_path)

    async def parse_filename(self, file_path: Path) -> MusicInfo:
        """解析文件名"""
        return self.filename_parser.parse(file_path)

    async def query_musicbrainz(
        self, artist: str, title: str, album: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        查询 MusicBrainz

        Args:
            artist: 艺术家名称
            title: 曲目标题
            album: 专辑名称

        Returns:
            MusicBrainz 查询结果
        """
        query = f"{artist} {title}"
        if album:
            query = f"{artist} {album} {title}"

        self.logger.info(f"查询 MusicBrainz: {query}")

        # 搜索曲目
        tracks = await self.run_module("musicbrainz", "search_track", query, limit=10)

        if not tracks:
            self.logger.info("MusicBrainz 未找到匹配曲目")
            return None

        # 获取曲目详情
        track_id = tracks[0].get("id")
        track_info = await self.run_module("musicbrainz", "get_track_info", track_id)

        if not track_info:
            return None

        # 获取艺术家信息
        artist_credit = track_info.get("artist_credit")
        if artist_credit and artist_credit.get("id"):
            artist_info = await self.run_module(
                "musicbrainz", "get_artist_info", artist_credit["id"]
            )
            track_info["artist_info"] = artist_info

        return track_info

    def merge_metadata(
        self, local: MusicInfo, filename: MusicInfo, online: Optional[Dict[str, Any]]
    ) -> MusicInfo:
        """
        合并元数据（优先级：在线 > 本地 > 文件名）
        """
        merged = MusicInfo()

        merged.artist = (
            online.get("artist_credit", {}).get("name")
            if online
            else (local.artist or filename.artist)
        )
        merged.album = (
            online.get("artist_credit", {}).get("name")
            if online
            else (local.album or filename.album)
        )
        merged.title = online.get("title") if online else (local.title or filename.title)

        merged.path = local.path
        merged.file_format = local.file_format
        merged.file_size = local.file_size
        merged.bitrate = local.bitrate
        merged.sample_rate = local.sample_rate
        merged.channels = local.channels
        merged.duration = local.duration or filename.duration
        merged.track_number = local.track_number or filename.track_number
        merged.disc_number = local.disc_number
        merged.position = local.position

        if online:
            artist_info = online.get("artist_info", {})
            merged.musicbrainz_artist_id = artist_info.get("id")
            merged.musicbrainz_track_id = online.get("id")

        merged.genres = local.genres or filename.genres
        merged.tags = local.tags or filename.tags
        merged.lyrics = local.lyrics

        return merged

    async def complete(self, metadata: MusicInfo, fetch_cover: bool = True) -> MusicInfo:
        """补全元数据"""
        cache_key = f"metadata:{metadata.musicbrainz_track_id or metadata.path}"
        cached = self.get_cache(cache_key)
        if cached:
            self.logger.debug(f"使用缓存的元数据: {metadata.title}")
            return cached

        # 查询 MusicBrainz
        if metadata.artist and metadata.title:
            online = await self.query_musicbrainz(metadata.artist, metadata.title, metadata.album)
            if online:
                metadata = self.merge_metadata(metadata, metadata, online)

        self.set_cache(cache_key, metadata, ttl=86400)
        self.logger.info(f"补全元数据: {metadata.title}")
        return metadata

    async def save_to_database(self, metadata: MusicInfo) -> Dict[str, Any]:
        """保存到数据库"""
        artist_oper = ArtistOper(db_manager)
        album_oper = AlbumOper(db_manager)
        track_oper = TrackOper(db_manager)

        result = {}

        # 保存艺术家
        artist = None
        if metadata.musicbrainz_artist_id:
            artist = await artist_oper.get_by_musicbrainz_id(metadata.musicbrainz_artist_id)

        if not artist and metadata.artist:
            artist = await artist_oper.create(
                name=metadata.artist,
                musicbrainz_id=metadata.musicbrainz_artist_id,
                image_url=metadata.cover_url,
            )
            self.logger.info(f"创建艺术家: {artist.name} (ID: {artist.id})")

        if artist:
            result["artist_id"] = artist.id

        # 保存专辑
        album = None
        if metadata.album and artist:
            albums = await album_oper.get_by_artist_id(artist.id)
            album = next((a for a in albums if a.title == metadata.album), None)

        if not album and metadata.album and artist:
            album = await album_oper.create(
                artist_id=artist.id,
                title=metadata.album,
                cover_url=metadata.cover_url,
                genres=metadata.genres,
                track_number=metadata.track_number,
                total_duration=metadata.duration,
            )
            self.logger.info(f"创建专辑: {album.title} (ID: {album.id})")

        if album:
            result["album_id"] = album.id

        # 保存曲目
        track = None
        if metadata.path:
            track = await track_oper.get_by_path(metadata.path)

        if not track:
            track = await track_oper.create(
                title=metadata.title or "Unknown",
                artist_id=artist.id if artist else None,
                album_id=album.id if album else None,
                path=metadata.path,
                file_format=metadata.file_format,
                file_size=metadata.file_size,
                bitrate=metadata.bitrate,
                sample_rate=metadata.sample_rate,
                channels=metadata.channels,
                duration=metadata.duration,
                track_number=metadata.track_number,
                disc_number=metadata.disc_number,
                musicbrainz_track_id=metadata.musicbrainz_track_id,
                genres=metadata.genres,
                tags=metadata.tags,
                lyrics=metadata.lyrics,
            )
            self.logger.info(f"创建曲目: {track.title} (ID: {track.id})")

        if track:
            result["track_id"] = track.id

        return result

    async def batch_recognize(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """批量识别元数据"""
        self.logger.info(f"批量识别 {len(file_paths)} 个文件")
        results = []

        for file_path in file_paths:
            path = Path(file_path)
            try:
                local_metadata = await self.extract_local_metadata(path)
                filename_metadata = await self.parse_filename(path)
                metadata = self.merge_metadata(local_metadata, filename_metadata, None)
                completed_metadata = await self.complete(metadata)
                save_result = await self.save_to_database(completed_metadata)

                results.append(
                    {
                        "path": str(path),
                        "success": True,
                        "metadata": completed_metadata.to_dict(),
                        "save_result": save_result,
                    }
                )
            except Exception as e:
                self.logger.error(f"识别文件失败: {file_path}, 错误: {e}")
                results.append(
                    {
                        "path": file_path,
                        "success": False,
                        "error": str(e),
                    }
                )

        self.logger.info(f"批量识别完成，成功 {len([r for r in results if r['success']])} 个")
        return results

    async def rewrite_metadata(self, track_id: int) -> bool:
        """将识别结果写入音频文件"""
        self.logger.info(f"回写元数据到文件: {track_id}")

        track_oper = TrackOper(db_manager)
        track = await track_oper.get_by_id(track_id)

        if not track or not track.path:
            self.logger.warning("曲目或文件路径不存在")
            return False

        try:
            import mutagen

            audio_file = mutagen.File(track.path)
            audio_file.delete()

            if track.title:
                audio_file["TIT2"] = track.title
            if track.artist_id:
                artist_oper = ArtistOper(db_manager)
                artist = await artist_oper.get_by_id(track.artist_id)
                if artist:
                    audio_file["TPE1"] = artist.name
            if track.album_id:
                album_oper = AlbumOper(db_manager)
                album = await album_oper.get_by_id(track.album_id)
                if album:
                    audio_file["TALB"] = album.title
            if track.track_number:
                audio_file["TRCK"] = f"{track.track_number}"
            if track.genres:
                audio_file["TCON"] = track.genres[0]
            if track.lyrics:
                audio_file["USLT"] = f"eng\n{track.lyrics}"

            audio_file.save()
            self.logger.info(f"元数据回写成功: {track.path}")
            return True
        except Exception as e:
            self.logger.error(f"元数据回写失败: {e}")
            return False
