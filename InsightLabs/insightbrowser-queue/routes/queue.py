"""
队列路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from services.queue import get_queue

router = APIRouter(prefix="/api/v1/queue", tags=["Queue"])

_queue = get_queue()


class SubmitRequest(BaseModel):
    user_request: str = Field(..., min_length=1)
    priority: int = Field(default=3, ge=1, le=5)
    agent_id: str = Field(default="unknown")


@router.post("/submit")
async def submit_task(req: SubmitRequest):
    task = _queue.submit(req.user_request, req.priority, req.agent_id)
    return {
        "success": True,
        "task_id": task.task_id,
        "status": task.status,
        "priority": task.priority,
    }


@router.get("/task/{task_id}")
async def get_task(task_id: str):
    task = _queue.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return {"task": task.to_dict()}


@router.get("/tasks/{agent_id}")
async def list_tasks(agent_id: str, status: Optional[str] = None):
    tasks = _queue.list_tasks(agent_id, status)
    return {"tasks": tasks, "total": len(tasks)}


@router.get("/stats")
async def queue_stats():
    return {"success": True, ** _queue.stats()}
