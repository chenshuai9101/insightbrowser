"""insightbrowser-approval — Approval Workflow (Port 7015)"""
import uvicorn
from fastapi import FastAPI
from routes.approval import router as approval_router

app = FastAPI(title="InsightBrowser Approval Workflow", version="1.0.0")
app.include_router(approval_router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "approval", "port": 7015}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7015, log_level="info")
