"""
Site Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SiteBase(BaseModel):
    """站点基础模型"""
    name: str = Field(..., description="站点名称")
    domain: Optional[str] = Field(None, description="站点域名")
    url: str = Field(..., description="站点URL")
    cookie: Optional[str] = Field(None, description="Cookie")
    passkey: Optional[str] = Field(None, description="Passkey")
    username: Optional[str] = Field(None, description="用户名")
    password: Optional[str] = Field(None, description="密码")
    proxy: Optional[str] = Field(None, description="代理")
    ua: Optional[str] = Field(None, description="User-Agent")
    timeout: int = Field(30, description="超时时间（秒）")
    rss: Optional[str] = Field(None, description="RSS地址")
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
    name: Optional[str] = None
    domain: Optional[str] = None
    url: Optional[str] = None
    cookie: Optional[str] = None
    passkey: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    proxy: Optional[str] = None
    ua: Optional[str] = None
    timeout: Optional[int] = None
    rss: Optional[str] = None
    rss_interval: Optional[int] = None
    downloader: Optional[str] = None
    priority: Optional[int] = None
    enabled: Optional[bool] = None
    site_type: Optional[str] = None


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