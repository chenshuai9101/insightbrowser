#!/usr/bin/env python3
"""InsightBrowser Registry - AHP Protocol Agent Directory Service"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os

from config import (
    HOST, PORT, STATIC_DIR, TEMPLATES_DIR,
    ASSETS_DIR, PLATFORM_NAME, PLATFORM_DESCRIPTION,
    PLATFORM_VERSION,
)
from routes.api import router as api_router
from routes.pages import router as pages_router, init_templates
from services.registry import bootstrap

# Create FastAPI app
app = FastAPI(
    title=PLATFORM_NAME,
    description=PLATFORM_DESCRIPTION,
    version=PLATFORM_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Mount static files
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Mount assets (QR codes, etc.)
if os.path.isdir(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

# Initialize templates
init_templates(TEMPLATES_DIR)

# Register routers
app.include_router(pages_router)
app.include_router(api_router)


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    bootstrap()
    print(f"  ✅ Database initialized")


if __name__ == "__main__":
    import uvicorn
    reload_enabled = os.getenv("INSIGHTBROWSER_RELOAD", "0") == "1"
    print(f"""
🔍 {PLATFORM_NAME} v{PLATFORM_VERSION}
{'=' * 50}
  Home:    http://localhost:{PORT}
  API:     http://localhost:{PORT}/api
  Docs:    http://localhost:{PORT}/docs
  Reload:  {"on" if reload_enabled else "off"}
{'=' * 50}
""")
    uvicorn.run("main:app", host=HOST, port=PORT, reload=reload_enabled)
