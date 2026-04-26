#!/usr/bin/env python3
"""InsightBrowser Commerce Bridge - Merchant Onboarding Service

Merchants paste a URL → system auto-generates agent.json →
registers with Registry (7000) + Hosting (7001).

Usage:
    cd insightbrowser-commerce && python3 main.py

Starts on http://localhost:7004
"""
import logging
import sys
import os

# ─── Path Setup ────────────────────────────────────────────────────────
# For uvicorn subprocess: __file__ may not be defined when imported,
# so we use sys.argv[0] as anchor.
_anchor = None
for candidate in [
    os.environ.get("COMMERCE_BRIDGE_DIR"),
    os.path.abspath(__file__) if '__file__' in dir() else None,
    os.path.abspath(sys.argv[0]) if sys.argv and sys.argv[0] else None,
]:
    if candidate:
        _anchor = os.path.dirname(candidate) if os.path.isfile(candidate) else candidate
        break

if _anchor is None:
    _anchor = os.getcwd()

_COMMERCE_DIR = _anchor
_PARENT_DIR = os.path.dirname(_COMMERCE_DIR)
_AHP_DIR = os.path.join(_PARENT_DIR, "insightbrowser-ahp")

# Insert order is CRITICAL: commerce dir MUST be at sys.path[0] to avoid
# Python resolving `import routes.api` from insightbrowser-ahp/routes/.
# Insert in reverse priority so commerce ends up first.
for p in [_AHP_DIR, _PARENT_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)
# commerce dir always goes to position 0
sys.path.insert(0, _COMMERCE_DIR)


# ─── App Imports ───────────────────────────────────────────────────────
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.api import router as api_router
from routes.pages import router as pages_router


# ─── Logging ───────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("commerce")

# ─── App ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="InsightBrowser Commerce Bridge",
    description="商家入驻网关 — 粘贴URL，自动生成Agent配置并注册系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(pages_router)
app.include_router(api_router)


# ─── Root ──────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "commerce-bridge",
        "version": "1.0.0",
    }


# ─── Startup ───────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    logger.info("""
╔══════════════════════════════════════════════╗
║   InsightBrowser Commerce Bridge v1.0       ║
║   商家入驻网关                                ║
║                                              ║
║   Port:      7004                            ║
║   Service:   commerce-bridge                 ║
║   Registry:  http://localhost:7000           ║
║   Hosting:   http://localhost:7001           ║
║                                              ║
║   UI:        http://localhost:7004           ║
║   API:       http://localhost:7004/docs      ║
╚══════════════════════════════════════════════╝
    """)


# ─── Entrypoint ────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.environ["COMMERCE_BRIDGE_DIR"] = _COMMERCE_DIR
    uvicorn.run(app, host="0.0.0.0", port=7004)
