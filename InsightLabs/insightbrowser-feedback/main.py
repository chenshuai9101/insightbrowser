"""insightbrowser-feedback — Agent Feedback System (Port 7016)"""
import uvicorn
from fastapi import FastAPI
from routes.feedback import router as fb_router

app = FastAPI(title="InsightBrowser Feedback", version="1.0.0")
app.include_router(fb_router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "feedback", "port": 7016}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7016, log_level="info")
