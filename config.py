"""InsightBrowser Registry - Configuration"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Server
HOST = os.getenv("INSIGHTBROWSER_HOST", "127.0.0.1")
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
PLATFORM_VERSION = "2.0.0"

# SSRF 防护（见 models.is_safe_target_url）：
# 默认放行回环地址（单机部署/本地冒烟测试需要），
# 公网部署请设置 INSIGHTBROWSER_STRICT_SSRF=1 连回环一起拦截。
STRICT_SSRF = os.getenv("INSIGHTBROWSER_STRICT_SSRF", "0") == "1"
