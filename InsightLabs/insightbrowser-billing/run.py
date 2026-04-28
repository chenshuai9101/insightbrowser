#!/usr/bin/env python3
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import uvicorn
from main import app
uvicorn.run(app, host="0.0.0.0", port=7006)
