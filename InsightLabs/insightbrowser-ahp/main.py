#!/usr/bin/env python3
"""InsightBrowser AHP - AHP Protocol Proxy Engine

Provides AHP v0.1 endpoints for sites hosted on InsightBrowser Hosting.
Acts as a proxy, routing requests to the appropriate backend engine
(InsightSee, InsightLens, or generic).

Usage:
    python3 main.py

This starts the service on http://localhost:7002
"""
import logging
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.ahp import router as ahp_router

# ─── Logging ───────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("ahp")

# ─── App ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="InsightBrowser AHP Proxy",
    description="AHP Protocol Proxy Engine — Routes agent requests to "
                "InsightSee, InsightLens, and other backend engines",
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
app.include_router(ahp_router)


# ─── Root endpoint ─────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "service": "InsightBrowser AHP Proxy",
        "version": "1.0.0",
        "protocol": "ahp/0.1",
        "endpoints": {
            "list_sites": "/sites",
            "site_agent_json": "/sites/{site_id}",
            "site_info": "/sites/{site_id}/info",
            "site_action": "/sites/{site_id}/action",
            "site_data": "/sites/{site_id}/data",
            "site_stream": "/sites/{site_id}/stream",
        },
        "docs": "/docs",
    }


# ─── Health check ──────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ahp-proxy"}


# ─── Startup ───────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    logger.info("""
╔══════════════════════════════════════════════╗
║     InsightBrowser AHP Proxy v1.0           ║
║     AHP Protocol Proxy Engine               ║
║                                              ║
║   Port:      7002                            ║
║   Protocol:  ahp/0.1                        ║
║   Backends:  InsightSee, InsightLens        ║
║                                              ║
║   API:       http://localhost:7002/sites     ║
║   Docs:      http://localhost:7002/docs      ║
╚══════════════════════════════════════════════╝
    """)


# ─── Entrypoint ────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7002, reload=True)
