"""
InsightBrowser Billing — Agent 计费与支付网关
端口: 7006
"""
from fastapi import FastAPI
import uvicorn
from routes.billing import router as billing_router
from routes.payment import router as payment_router

app = FastAPI(title="InsightBrowser Billing", version="1.0.0")
app.include_router(billing_router)
app.include_router(payment_router)


@app.get("/")
async def root():
    return {
        "service": "InsightBrowser Billing",
        "version": "1.0.0",
        "ports": {"metering": "/api/v1/billing", "escrow": "/api/v1/billing/escrow"},
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7006)
