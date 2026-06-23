"""
AHP Protocol Channel
Backends: [insightbrowser-ahp, A2A bridge, MCP bridge]
"""
from channels import Channel, Backend, registry


def check_ahp_service() -> dict:
    """Check if AHP protocol service is available."""
    import socket
    for port in [7000, 7024]:  # Registry + AIP-Bridge
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()
            if result == 0:
                return {"status": "online", "port": port}
        except Exception:
            pass
    return {"status": "offline", "error": "no AHP service found"}


ahp_channel = Channel(
    name="ahp",
    icon="🔌",
    description="AHP 协议层 - Agent 间通信与能力发现",
    backends=[
        Backend("insightbrowser-ahp", "AHP 协议引擎 (Registry)", check_ahp_service),
    ]
)


def register(reg):
    reg.register(ahp_channel)
