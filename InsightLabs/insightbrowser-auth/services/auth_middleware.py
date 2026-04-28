"""
认证中间件 — 可被其他 InsightLabs 服务复用
"""
from fastapi import Request, HTTPException
from services.auth import get_auth

_auth = get_auth()


async def auth_middleware(request: Request, call_next):
    """FastAPI 中间件：验证请求的 API Key"""
    # 开发模式：没有注册任何 Agent 时允许无认证
    agents = _auth.list_agents()
    if not agents:
        return await call_next(request)

    # 公开端点白名单
    public_paths = ["/docs", "/openapi.json", "/", "/health"]
    for p in public_paths:
        if request.url.path == p or request.url.path.startswith(p):
            return await call_next(request)

    # 注册端点允许无认证
    if request.url.path.endswith("/auth/register"):
        return await call_next(request)

    auth_header = request.headers.get("Authorization") or request.headers.get("X-Api-Key", "")
    agent = _auth.verify_header(auth_header)
    if not agent:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")

    request.state.agent_id = agent["agent_id"]
    request.state.agent_role = agent.get("role", "agent")
    return await call_next(request)


def require_role(*roles: str):
    """装饰器：要求特定角色"""
    from functools import wraps
    from fastapi import Request, HTTPException

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request") or (args[0] if args and isinstance(args[0], Request) else None)
            if request and hasattr(request.state, "agent_role"):
                if request.state.agent_role not in roles and "admin" not in [request.state.agent_role, *roles]:
                    raise HTTPException(status_code=403, detail=f"Role required: {' or '.join(roles)}")
            return await func(*args, **kwargs)
        return wrapper
    return decorator
