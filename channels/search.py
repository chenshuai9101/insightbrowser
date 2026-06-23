"""
Search Engine Channel
Backends: [insightbrowser-search (7020), Exa via MCP, DuckDuckGo]
"""
from channels import Channel, Backend, registry


def check_search_service() -> dict:
    """Check if our own search service (7020) is available."""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.5)
        result = sock.connect_ex(("127.0.0.1", 7020))
        sock.close()
        if result == 0:
            return {"status": "online"}
        return {"status": "offline", "error": "port 7020 not responding"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def check_exa_mcp() -> dict:
    """Check if Exa via MCP is available."""
    import shutil
    mcporter = shutil.which("mcporter")
    if mcporter:
        return {"status": "online", "note": "mcporter found"}
    return {"status": "offline", "error": "mcporter not installed"}


search_channel = Channel(
    name="search",
    icon="🔍",
    description="语义搜索引擎 - Agent 发现/全网检索",
    backends=[
        Backend("insightbrowser-search", "自有语义搜索服务", check_search_service),
        Backend("exa-mcp", "Exa AI 语义搜索 (MCP)", check_exa_mcp),
    ]
)


def register(reg):
    reg.register(search_channel)
