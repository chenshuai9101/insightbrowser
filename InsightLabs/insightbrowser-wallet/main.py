"""insightbrowser-wallet — Agent Wallet Service (Port 7013)"""
import uvicorn
from fastapi import FastAPI
from routes.wallet import router as wallet_router

app = FastAPI(title="InsightBrowser Wallet", version="1.0.0")
app.include_router(wallet_router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "wallet", "port": 7013}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7013, log_level="info")
