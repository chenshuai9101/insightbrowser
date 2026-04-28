"""insightbrowser-bi — BI Dashboard (Port 7018)"""
import uvicorn
from fastapi import FastAPI
from routes.bi import router as bi_router

app = FastAPI(title="InsightBrowser BI", version="1.0.0")
app.include_router(bi_router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "bi", "port": 7018}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7018, log_level="info")
