"""
任务队列 — 异步调度、优先级、并发控制
"""
import asyncio
import logging
import random
import string
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("queue")


class Task:
    def __init__(self, user_request: str, priority: int = 3, agent_id: str = "unknown"):
        self.task_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        self.user_request = user_request
        self.priority = priority  # 1-5, 1最高
        self.agent_id = agent_id
        self.status = "pending"
        self.created_at = datetime.now().isoformat()
        self.started_at = None
        self.completed_at = None
        self.result = None
        self.error = None
        self.retries = 0
        self.max_retries = 3

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "user_request": self.user_request[:200],
            "priority": self.priority,
            "agent_id": self.agent_id,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "result": self.result[:500] if self.result else None,
            "error": self.error,
            "retries": self.retries,
        }


class TaskQueue:
    def __init__(self, max_concurrent: int = 10):
        self._queue: List[Task] = []
        self._tasks: Dict[str, Task] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self.max_concurrent = max_concurrent
        self._done_count = 0
        self._failed_count = 0
        self._total_count = 0

    def submit(self, user_request: str, priority: int = 3, agent_id: str = "unknown") -> Task:
        task = Task(user_request, priority, agent_id)
        self._tasks[task.task_id] = task
        self._queue.append(task)
        self._total_count += 1
        # 按优先级排序（数字越小优先级越高）
        self._queue.sort(key=lambda t: t.priority)
        return task

    def next(self) -> Optional[Task]:
        """取出下一个待执行任务"""
        for task in self._queue:
            if task.status == "pending":
                return task
        return None

    def get(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def list_tasks(self, agent_id: str = None, status: str = None) -> List[dict]:
        tasks = list(self._tasks.values())
        if agent_id:
            tasks = [t for t in tasks if t.agent_id == agent_id]
        if status:
            tasks = [t for t in tasks if t.status == status]
        return [t.to_dict() for t in tasks[-50:]]

    def stats(self) -> dict:
        pending = sum(1 for t in self._tasks.values() if t.status == "pending")
        running = sum(1 for t in self._tasks.values() if t.status == "running")
        return {
            "pending": pending,
            "running": running,
            "done": self._done_count,
            "failed": self._failed_count,
            "total": self._total_count,
            "max_concurrent": self.max_concurrent,
        }


_queue = TaskQueue(max_concurrent=10)

def get_queue() -> TaskQueue:
    return _queue
