"""insightbrowser-benchmark — Agent Benchmark (Port 7019)"""
import uvicorn
from fastapi import FastAPI
from routes.benchmark import router as bm_router

app = FastAPI(title="InsightBrowser Benchmark", version="1.0.0")
app.include_router(bm_router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "benchmark", "port": 7019}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7019, log_level="info")
