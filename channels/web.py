"""
Web Reading Channel
Backends: [Jina Reader, Firecrawl, requests+BeautifulSoup]
Inspired by Agent-Reach's web.py
"""
from channels import Channel, Backend, registry
import shutil


def check_jina_reader() -> dict:
    """Check if Jina Reader is accessible."""
    import requests
    try:
        resp = requests.get("https://r.jina.ai/http://example.com", timeout=3)
        if resp.status_code < 500:
            return {"status": "online"}
        return {"status": "offline", "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"status": "offline", "error": str(e)}


def check_curl() -> dict:
    """Basic curl as fallback."""
    curl = shutil.which("curl")
    if curl:
        return {"status": "online", "note": "curl available"}
    return {"status": "offline", "error": "curl not installed"}


web_channel = Channel(
    name="web",
    icon="🌐",
    description="网页读取 - Agent 获取互联网内容",
    backends=[
        Backend("jina-reader", "Jina AI Reader (免费, 无需API Key)", check_jina_reader),
        Backend("curl", "基础 HTTP 请求", check_curl),
    ]
)


def register(reg):
    reg.register(web_channel)
