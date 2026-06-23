"""
Wallet & Commerce Channel
Backends: [insightbrowser-wallet (7013), insightbrowser-commerce (7025)]
"""
from channels import Channel, Backend, registry


def check_wallet() -> dict:
    """Check if wallet service (7013) is available."""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.5)
        result = sock.connect_ex(("127.0.0.1", 7013))
        sock.close()
        if result == 0:
            return {"status": "online"}
        return {"status": "offline", "error": "port 7013 not responding"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def check_commerce() -> dict:
    """Check if commerce service (7025) is available."""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.5)
        result = sock.connect_ex(("127.0.0.1", 7025))
        sock.close()
        if result == 0:
            return {"status": "online"}
        return {"status": "offline", "error": "port 7025 not responding"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


wallet_channel = Channel(
    name="wallet",
    icon="💰",
    description="Agent 经济系统 - 钱包 + 交易市场",
    backends=[
        Backend("insightbrowser-wallet", "Agent 钱包 (7013)", check_wallet),
        Backend("insightbrowser-commerce", "Agent 交易市场 (7025)", check_commerce),
    ]
)


def register(reg):
    reg.register(wallet_channel)
