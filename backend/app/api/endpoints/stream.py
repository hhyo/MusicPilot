"""
音频流 API 端点
音频文件流式传输
"""

from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.db.operations.track import TrackOper
from app.core.config import settings
from app.core.log import logger
from app.schemas.response import ResponseModel

router = APIRouter()


def get_track_oper(db: AsyncSession = Depends(get_db)) -> TrackOper:
    """获取 Track 操作实例"""
    from app.db import db_manager

    return TrackOper(db_manager)


def parse_range_header(range_header: str, file_size: int) -> tuple[int, int]:
    """
    解析 Range 请求头

    Args:
        range_header: Range 请求头（如 "bytes=0-1023"）
        file_size: 文件总大小

    Returns:
        (start, end) 字节范围
    """
    if not range_header:
        return 0, file_size - 1

    if range_header.startswith("bytes="):
        range_header = range_header[6:]

    # 支持 "bytes=start-end" 格式
    if "-" in range_header:
        parts = range_header.split("-")
        if len(parts) == 2:
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if parts[1] else file_size - 1
            # 修正范围
            start = max(0, min(start, file_size - 1))
            end = max(start, min(end, file_size - 1))
            return start, end

    return 0, file_size - 1


async def get_audio_file_bytes(file_path: Path, start: int, end: int) -> bytes:
    """
    获取音频文件的指定字节范围

    Args:
        file_path: 文件路径
        start: 起始字节
        end: 结束字节

    Returns:
        文件字节数据
    """
    with open(file_path, "rb") as f:
        f.seek(start)
        return f.read(end - start + 1)


def get_mime_type(file_format: str) -> str:
    """
    获取音频格式的 MIME 类型

    Args:
        file_format: 文件格式（如 "mp3", "flac", "m4a"）

    Returns:
        MIME 类型
    """
    mime_types = {
        "mp3": "audio/mpeg",
        "flac": "audio/flac",
        "m4a": "audio/mp4",
        "ogg": "audio/ogg",
        "wav": "audio/wav",
        "aac": "audio/aac",
    }
    return mime_types.get(file_format.lower(), "audio/mpeg")


@router.get("/tracks/{track_id}/stream")
async def stream_track(
    track_id: int,
    request: Request,
    format: Optional[str] = Query(None, description="目标格式（如需要转换）"),
    track_oper: TrackOper = Depends(get_track_oper),
):
    """
    流式传输曲目

    - **track_id**: 曲目 ID
    - **format**: 目标格式（可选，如需要转换，支持 mp3/flac/m4a）
    - **Range**: 支持 Range 请求头进行断点续传

    支持的音频格式：mp3, flac, m4a, ogg, wav
    """
    # 查询曲目
    track = await track_oper.get_by_id(track_id)
    if not track:
        raise HTTPException(status_code=404, detail="曲目不存在")

    if not track.path:
        raise HTTPException(status_code=404, detail="曲目文件路径不存在")

    file_path = Path(track.path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="曲目文件不存在")

    file_size = file_path.stat().st_size
    file_format = track.file_format or "mp3"

    # 检查是否需要格式转换（暂时不支持转换，直接返回原格式）
    # TODO: 使用 ffmpeg 实现音频格式转换
    if format and format.lower() != file_format.lower():
        raise HTTPException(status_code=400, detail=f"格式转换暂未实现，当前格式: {file_format}")

    # 解析 Range 请求头
    range_header = request.headers.get("Range")
    start, end = parse_range_header(range_header, file_size)

    # 设置响应头
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Type": get_mime_type(file_format),
        "Content-Disposition": f'inline; filename="{track.title}.{file_format}"',
    }

    # 如果是 Range 请求，返回部分内容
    if range_header:
        content_length = end - start + 1
        headers.update(
            {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Content-Length": str(content_length),
            }
        )
        status_code = 206  # Partial Content
    else:
        content_length = file_size
        headers["Content-Length"] = str(content_length)
        status_code = 200

    # 流式传输文件内容
    async def file_iterator():
        """文件迭代器"""
        with open(file_path, "rb") as f:
            f.seek(start)
            remaining = end - start + 1
            chunk_size = 64 * 1024  # 64KB chunks
            while remaining > 0:
                chunk = f.read(min(chunk_size, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    # 记录流式传输日志
    logger.info(f"流式传输: {track.title} ({track_id}), 范围: {start}-{end}/{file_size}")

    return StreamingResponse(
        file_iterator(),
        status_code=status_code,
        headers=headers,
        media_type=get_mime_type(file_format),
    )


@router.get("/tracks/{track_id}/stream-info", response_model=ResponseModel[dict])
async def get_stream_info(
    track_id: int,
    track_oper: TrackOper = Depends(get_track_oper),
):
    """
    获取曲目流式传输信息

    返回文件大小、格式、是否支持 Range 请求等信息
    """
    track = await track_oper.get_by_id(track_id)
    if not track:
        raise HTTPException(status_code=404, detail="曲目不存在")

    if not track.path:
        raise HTTPException(status_code=404, detail="曲目文件路径不存在")

    file_path = Path(track.path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="曲目文件不存在")

    file_size = file_path.stat().st_size

    return ResponseModel(
        data={
            "track_id": track_id,
            "title": track.title,
            "file_size": file_size,
            "file_format": track.file_format,
            "duration": track.duration,
            "supports_range": True,
            "mime_type": get_mime_type(track.file_format or "mp3"),
        }
    )


@router.get("/tracks/{track_id}/download", response_class=StreamingResponse)
async def download_track(
    track_id: int,
    track_oper: TrackOper = Depends(get_track_oper),
):
    """
    下载曲目文件

    返回完整的音频文件用于下载
    """
    track = await track_oper.get_by_id(track_id)
    if not track:
        raise HTTPException(status_code=404, detail="曲目不存在")

    if not track.path:
        raise HTTPException(status_code=404, detail="曲目文件路径不存在")

    file_path = Path(track.path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="曲目文件不存在")

    file_size = file_path.stat().st_size
    file_format = track.file_format or "mp3"

    headers = {
        "Content-Type": get_mime_type(file_format),
        "Content-Disposition": f'attachment; filename="{track.title}.{file_format}"',
        "Content-Length": str(file_size),
    }

    async def file_iterator():
        """文件迭代器"""
        with open(file_path, "rb") as f:
            chunk_size = 64 * 1024  # 64KB chunks
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    logger.info(f"下载曲目: {track.title} ({track_id})")

    return StreamingResponse(
        file_iterator(),
        headers=headers,
        media_type=get_mime_type(file_format),
    )
