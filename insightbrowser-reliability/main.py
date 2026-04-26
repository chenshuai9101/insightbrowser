#!/usr/bin/env python3
"""InsightBrowser Reliability — Trust Registry & Credit Ledger

L3 of the InsightLabs architecture. Provides:
1. Reliability Registry (trust ratings, heartbeat health checks)
2. Credit Ledger (agent-to-agent call accounting)
3. Integration with AHP Proxy and SDK

Usage:
    python3 main.py

Runs on http://localhost:7003
"""
import logging
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models import init_db
from routes.trust import router as trust_router
from routes.ledger import router as ledger_router
from services.heartbeater import heartbeater

# ─── Logging ───────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("reliability")

# ─── App ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="InsightBrowser Reliability Registry",
    description="Trust ratings, heartbeat health checks, and credit ledger "
                "for the InsightBrowser Agent Network",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(trust_router)
app.include_router(ledger_router)


# ─── Root Endpoint ─────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "service": "InsightBrowser Reliability Registry",
        "version": "1.0.0",
        "modules": {
            "trust_registry": "/api/trust/{site_id}",
            "global_stats": "/api/stats",
            "leaderboard": "/api/leaderboard",
            "dashboard": "/api/dashboard",
            "heartbeat": "/api/heartbeat/{site_id}",
            "ledger_record": "/api/ledger/record",
            "ledger_transactions": "/api/ledger/transactions",
            "ledger_balance": "/api/ledger/agent/{agent_id}/balance",
            "ledger_leaderboard": "/api/ledger/leaderboard",
        },
        "docs": "/docs",
    }


# ─── Health Check ──────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "reliability-registry"}


# ─── Startup ───────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    logger.info("Initializing database...")
    init_db()

    logger.info("Starting heartbeat engine...")
    await heartbeater.start()

    logger.info("""
╔══════════════════════════════════════════════════╗
║  InsightBrowser Reliability Registry v1.0       ║
║  Trust + Credit Layer for Agent Networks        ║
║                                                  ║
║  Port:      7003                                 ║
║  Heartbeat: Every 30s                            ║
║  Ledger:    Credit-based call accounting         ║
║                                                  ║
║  API:       http://localhost:7003/docs           ║
╚══════════════════════════════════════════════════╝
    """)


# ─── Shutdown ──────────────────────────────────────────────────────────

@app.on_event("shutdown")
async def shutdown():
    logger.info("Stopping heartbeat engine...")
    await heartbeater.stop()


# ─── Entrypoint ────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7003, reload=True)
