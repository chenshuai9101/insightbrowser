"""insightbrowser-search — Semantic Search (Port 7020)"""
import uvicorn
from fastapi import FastAPI
from routes.search import router as search_router

app = FastAPI(title="InsightBrowser Search", version="1.0.0")
app.include_router(search_router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "search", "port": 7020}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7020, log_level="info")
