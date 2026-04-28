"""insightbrowser-matching — Agent Matching Engine (Port 7014)"""
import uvicorn
from fastapi import FastAPI
from routes.matching import router as matching_router

app = FastAPI(title="InsightBrowser Agent Matching", version="1.0.0")
app.include_router(matching_router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "matching", "port": 7014}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7014, log_level="info")
