"""
Matching Engine Channel
Backends: [insightbrowser-matching (7014), external matching API]
"""
from channels import Channel, Backend, registry


def check_matching_service() -> dict:
    """Check if matching engine (7014) is available."""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.5)
        result = sock.connect_ex(("127.0.0.1", 7014))
        sock.close()
        if result == 0:
            return {"status": "online"}
        return {"status": "offline", "error": "port 7014 not responding"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


matching_channel = Channel(
    name="matching",
    icon="🎯",
    description="智能匹配引擎 - 任务到 Agent 的最优分配",
    backends=[
        Backend("insightbrowser-matching", "自有匹配服务", check_matching_service),
    ]
)


def register(reg):
    reg.register(matching_channel)
