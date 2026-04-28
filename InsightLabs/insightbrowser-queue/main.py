"""
InsightBrowser Queue — 任务队列与异步调度
端口: 7008
"""
from fastapi import FastAPI
import uvicorn
from routes.queue import router as queue_router
from services.worker import start_worker

app = FastAPI(title="InsightBrowser Queue", version="1.0.0")
app.include_router(queue_router)


@app.on_event("startup")
async def on_startup():
    import asyncio
    asyncio.create_task(start_worker())


@app.get("/")
async def root():
    return {
        "service": "InsightBrowser Queue",
        "version": "1.0.0",
        "endpoints": {
            "submit": "/api/v1/queue/submit",
            "stats": "/api/v1/queue/stats",
        },
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7008)
