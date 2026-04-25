"""InsightBrowser Registry - Configuration"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Server
HOST = os.getenv("INSIGHTBROWSER_HOST", "0.0.0.0")
PORT = int(os.getenv("INSIGHTBROWSER_PORT", "7000"))

# Database
DATABASE_URL = os.path.join(BASE_DIR, "data", "registry.db")

# Static / Assets
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Seeds
SEEDS_DIR = os.path.join(BASE_DIR, "seeds")

# Platform info
PLATFORM_NAME = "InsightBrowser Registry"
PLATFORM_DESCRIPTION = "Agent原生互联网注册中心——AHP协议目录服务平台"
PLATFORM_VERSION = "0.1.0"
