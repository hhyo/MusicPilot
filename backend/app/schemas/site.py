"""
Site Schema
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SiteBase(BaseModel):
    """站点基础模型"""

    name: str = Field(..., description="站点名称")
    domain: str | None = Field(None, description="站点域名")
    url: str = Field(..., description="站点URL")
    cookie: str | None = Field(None, description="Cookie")
    passkey: str | None = Field(None, description="Passkey")
    username: str | None = Field(None, description="用户名")
    password: str | None = Field(None, description="密码")
    proxy: str | None = Field(None, description="代理")
    ua: str | None = Field(None, description="User-Agent")
    timeout: int = Field(30, description="超时时间（秒）")
    rss: str | None = Field(None, description="RSS地址")
    rss_interval: int = Field(60, description="RSS刷新间隔（秒）")
    downloader: str = Field("qbittorrent", description="下载器类型")
    priority: int = Field(1, description="优先级")
    enabled: bool = Field(True, description="是否启用")
    site_type: str = Field("resource", description="站点类型")


class SiteCreate(SiteBase):
    """创建站点"""

    pass


class SiteUpdate(BaseModel):
    """更新站点"""

    name: str | None = None
    domain: str | None = None
    url: str | None = None
    cookie: str | None = None
    passkey: str | None = None
    username: str | None = None
    password: str | None = None
    proxy: str | None = None
    ua: str | None = None
    timeout: int | None = None
    rss: str | None = None
    rss_interval: int | None = None
    downloader: str | None = None
    priority: int | None = None
    enabled: bool | None = None
    site_type: str | None = None


class SiteResponse(SiteBase):
    """站点响应模型"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SiteListResponse(BaseModel):
    """站点列表响应"""

    total: int
    items: list[SiteResponse]


class TestSiteRequest(BaseModel):
    """测试站点连接请求"""

    id: int = Field(..., description="站点ID")


class TestSiteResponse(BaseModel):
    """测试站点连接响应"""

    success: bool
    message: str
