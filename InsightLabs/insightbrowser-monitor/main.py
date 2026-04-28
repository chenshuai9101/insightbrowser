"""
InsightBrowser Monitor — 监控 & 告警仪表盘
端口: 7010
"""
import asyncio
from fastapi import FastAPI
import uvicorn
from routes.monitor import router as monitor_router
from services.monitor import _monitor, monitor_loop

app = FastAPI(title="InsightBrowser Monitor", version="1.0.0")
app.include_router(monitor_router)


@app.on_event("startup")
async def on_startup():
    # 启动时立即检查一次
    _monitor.check_all()
    # 后台每30秒检查
    asyncio.create_task(monitor_loop(30))


@app.get("/")
async def root():
    health = _monitor.check_all()
    return {
        "service": "InsightBrowser Monitor",
        "version": "1.0.0",
        "health": health,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7010)
