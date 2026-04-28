"""
InsightBrowser Auth — Agent 身份认证系统
端口: 7007
"""
from fastapi import FastAPI
import uvicorn
from routes.auth import router as auth_router

app = FastAPI(title="InsightBrowser Auth", version="1.0.0")
app.include_router(auth_router)


@app.get("/")
async def root():
    return {
        "service": "InsightBrowser Auth",
        "version": "1.0.0",
        "endpoints": {
            "register": "/api/v1/auth/register",
            "verify": "/api/v1/auth/verify",
            "agents": "/api/v1/auth/agents",
        },
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7007)
