"""
API v1 路由聚合
"""
from fastapi import APIRouter

# 创建 API 路由器
api_router = APIRouter()

# 注册各模块路由
from app.api.endpoints import artist, album, track, playlist, library, metadata, covers, stream, player, site, subscribe_release, subscribe

api_router.include_router(artist.router, prefix="/artists", tags=["artists"])
api_router.include_router(album.router, prefix="/albums", tags=["albums"])
api_router.include_router(track.router, prefix="/tracks", tags=["tracks"])
api_router.include_router(playlist.router, prefix="/playlists", tags=["playlists"])
api_router.include_router(library.router, prefix="/libraries", tags=["libraries"])
api_router.include_router(metadata.router, prefix="/metadata", tags=["metadata"])
api_router.include_router(covers.router, prefix="/covers", tags=["covers"])
api_router.include_router(stream.router, tags=["stream"])  # stream 路由带有完整前缀
api_router.include_router(player.router, prefix="/player", tags=["player"])
api_router.include_router(site.router, prefix="/sites", tags=["sites"])
api_router.include_router(subscribe_release.router, tags=["subscribe-releases"])
api_router.include_router(subscribe.router, prefix="/subscribes", tags=["subscribes"])

# TODO: 注册其他路由
# from app.api.endpoints import download, subscribe, media, system
# api_router.include_router(download.router, prefix="/download", tags=["download"])
# api_router.include_router(subscribe.router, prefix="/subscribes", tags=["subscribes"])
# api_router.include_router(media.router, prefix="/media", tags=["media"])
# api_router.include_router(system.router, prefix="/system", tags=["system"])

# 临时占位路由
@api_router.get("/")
async def api_v1_root():
    """API v1 根路径"""
    return {
        "message": "MusicPilot API v1",
        "version": "0.1.0",
        "endpoints": {
            "artists": "/api/v1/artists",
            "albums": "/api/v1/albums",
            "tracks": "/api/v1/tracks",
            "playlists": "/api/v1/playlists",
            "libraries": "/api/v1/libraries",
            "sites": "/api/v1/sites",
            "subscribe-releases": "/api/v1/subscribes/{subscribe_id}/releases",
        }
    }