"""insightbrowser-notify — Notification Service (Port 7021)"""
import uvicorn
from fastapi import FastAPI
from routes.notify import router as notify_router

app = FastAPI(title="InsightBrowser Notify", version="1.0.0")
app.include_router(notify_router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "notify", "port": 7021}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7021, log_level="info")
