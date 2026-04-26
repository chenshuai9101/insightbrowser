#!/usr/bin/env python3
"""Start Commerce Bridge - hardcoded paths edition."""
import sys, os
os.chdir("/Users/muyunye/.openclaw/workspace/InsightLabs/insightbrowser-commerce")
os.environ["COMMERCE_BRIDGE_DIR"] = os.getcwd()
import uvicorn
from main import app
uvicorn.run(app, host="0.0.0.0", port=7004, log_level="info")
