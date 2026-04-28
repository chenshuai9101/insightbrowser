"""
InsightBrowser Audit — 审计合规系统
端口: 7012
"""
from fastapi import FastAPI
import uvicorn
from routes.audit import router as audit_router

app = FastAPI(title="InsightBrowser Audit", version="1.0.0")
app.include_router(audit_router)


@app.get("/")
async def root():
    return {
        "service": "InsightBrowser Audit",
        "version": "1.0.0",
        "endpoints": {
            "record": "/api/v1/audit/record",
            "query": "/api/v1/audit/query",
            "chain": "/api/v1/audit/chain/{task_id}",
            "dispute": "/api/v1/audit/dispute",
            "violations": "/api/v1/audit/violations",
        },
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7012)
