"""
通用响应模型
定义统一的 API 响应格式
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ResponseModel(Generic[T], BaseModel):
    """通用响应模型"""

    success: bool = True
    message: str = "操作成功"
    data: T | None = None


class PaginatedResponse(Generic[T], BaseModel):
    """分页响应模型"""

    success: bool = True
    message: str = "查询成功"
    data: list[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0


class ErrorResponse(BaseModel):
    """错误响应模型"""

    success: bool = False
    message: str = "操作失败"
    error_code: str | None = None
    detail: str | None = None


class ValidationErrorDetail(BaseModel):
    """验证错误详情"""

    field: str
    message: str


class ValidationErrorResponse(BaseModel):
    """验证错误响应"""

    success: bool = False
    message: str = "数据验证失败"
    errors: list[ValidationErrorDetail] = []


# 常用响应别名
ArtistResponse = ResponseModel[Any]
AlbumResponse = ResponseModel[Any]
TrackResponse = ResponseModel[Any]
PlaylistResponse = ResponseModel[Any]
LibraryResponse = ResponseModel[Any]
DownloadResponse = ResponseModel[Any]
SubscribeResponse = ResponseModel[Any]
MediaServerResponse = ResponseModel[Any]
SystemConfigResponse = ResponseModel[Any]
