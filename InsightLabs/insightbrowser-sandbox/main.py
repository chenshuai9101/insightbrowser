"""insightbrowser-sandbox — Agent Sandbox (Port 7017)"""
import uvicorn
from fastapi import FastAPI
from routes.sandbox import router as sandbox_router

app = FastAPI(title="InsightBrowser Sandbox", version="1.0.0")
app.include_router(sandbox_router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "sandbox", "port": 7017}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7017, log_level="info")
