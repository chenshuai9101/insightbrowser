"""
任务工作器 — 从队列取任务 →调 Slots 流水线 →记录结果
"""
import asyncio
import aiohttp
import logging
from typing import Optional
from datetime import datetime
from services.queue import get_queue, Task

logger = logging.getLogger("worker")

SLOTS_PIPELINE_URL = "http://localhost:7005/api/v1/slots/pipeline"
METRICS_URL = "http://localhost:7005/api/v1/slots/metrics"


class TaskWorker:
    def __init__(self, queue, max_retries: int = 3):
        self.queue = queue
        self.max_retries = max_retries
        self._running = False
        self._session: Optional[aiohttp.ClientSession] = None

    async def start(self):
        self._running = True
        self._session = aiohttp.ClientSession()
        logger.info("Worker started")

        while self._running:
            task = self.queue.next()
            if task is None:
                await asyncio.sleep(1)
                continue

            async with self.queue._semaphore:
                await self._execute(task)

        if self._session:
            await self._session.close()

    async def _execute(self, task: Task):
        task.status = "running"
        task.started_at = datetime.now().isoformat()
        retry_delays = [2, 4, 8]  # 指数退避

        for attempt in range(self.max_retries + 1):
            try:
                async with self._session.post(SLOTS_PIPELINE_URL, json={
                    "user_request": task.user_request,
                    "max_steps": 20,
                }, timeout=aiohttp.ClientTimeout(total=300)) as resp:
                    result = await resp.json()

                if result.get("success"):
                    task.status = "done"
                    task.result = result.get("synthesis", {}).get("content", str(result))
                    task.completed_at = datetime.now().isoformat()
                    self.queue._done_count += 1
                    return
                else:
                    task.error = result.get("error", "Unknown error")
                    if attempt < self.max_retries:
                        task.retries = attempt + 1
                        await asyncio.sleep(retry_delays[min(attempt, len(retry_delays) - 1)])
                    else:
                        task.status = "failed"
                        task.completed_at = datetime.now().isoformat()
                        self.queue._failed_count += 1
                        return

            except asyncio.TimeoutError:
                task.error = "Task timeout (300s)"
                if attempt < self.max_retries:
                    task.retries = attempt + 1
                    await asyncio.sleep(retry_delays[min(attempt, len(retry_delays) - 1)])
                else:
                    task.status = "failed"
                    task.completed_at = datetime.now().isoformat()
                    self.queue._failed_count += 1
                    return
            except Exception as e:
                task.error = str(e)
                if attempt < self.max_retries:
                    task.retries = attempt + 1
                    await asyncio.sleep(retry_delays[min(attempt, len(retry_delays) - 1)])
                else:
                    task.status = "failed"
                    task.completed_at = datetime.now().isoformat()
                    self.queue._failed_count += 1
                    return

    async def stop(self):
        self._running = False
        if self._session:
            await self._session.close()
        logger.info("Worker stopped")


_worker: Optional[TaskWorker] = None

async def start_worker():
    global _worker
    q = get_queue()
    _worker = TaskWorker(q)
    asyncio.create_task(_worker.start())
