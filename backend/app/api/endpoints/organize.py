"""
Organize API 端点 - 文件整理管理
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.modules.organize.organize_module import OrganizeModule

router = APIRouter(prefix="/organize", tags=["文件整理"])
organize_module = OrganizeModule()


class TaskResponse(BaseModel):
    id: int
    status: str
    message: str = ""


class RetryResponse(BaseModel):
    message: str
    task_id: int


@router.get("/tasks", summary="获取整理任务列表")
async def get_organize_tasks():
    """获取整理任务列表"""
    return {"tasks": []}


@router.get("/tasks/{task_id}", summary="获取整理任务详情")
async def get_organize_task(task_id: int):
    """获取整理任务详情"""
    return {"task": {"id": task_id, "status": "pending"}}


@router.post("/tasks/{task_id}/retry", summary="重新整理任务")
async def retry_organize_task(task_id: int):
    """重新执行指定的整理任务"""
    return {"message": "任务已重新提交", "task_id": task_id}