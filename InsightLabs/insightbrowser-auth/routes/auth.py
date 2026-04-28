"""
认证路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from services.auth import get_auth
from services.permissions import get_perms

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

_auth = get_auth()
_perms = get_perms()


class RegisterRequest(BaseModel):
    agent_id: str = Field(..., min_length=2)
    metadata: dict = Field(default_factory=dict)


class GrantRequest(BaseModel):
    agent_id: str
    capability: str


class VerifyRequest(BaseModel):
    api_key: str


@router.post("/register")
async def register(req: RegisterRequest):
    result = _auth.register(req.agent_id, req.metadata)
    if not result["success"]:
        raise HTTPException(400, result["error"])
    # 默认授权基础能力
    _perms.grant(req.agent_id, "slots:basic")
    return result


@router.post("/verify")
async def verify(req: VerifyRequest):
    agent = _auth.verify(req.api_key)
    if not agent:
        return {"valid": False}
    return {
        "valid": True,
        "agent_id": agent["agent_id"],
        "role": agent["role"],
    }


@router.get("/agent/{agent_id}")
async def get_agent(agent_id: str):
    agent = _auth.get_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    caps = _perms.get_capabilities(agent_id)
    return {"agent": {"agent_id": agent["agent_id"], "role": agent["role"], "created_at": agent["created_at"]}, "capabilities": caps}


@router.post("/grant")
async def grant(req: GrantRequest):
    return _perms.grant(req.agent_id, req.capability)


@router.post("/revoke")
async def revoke(req: GrantRequest):
    return _perms.revoke(req.agent_id, req.capability)


@router.get("/check/{agent_id}/{capability}")
async def check(agent_id: str, capability: str):
    return {
        "agent_id": agent_id,
        "capability": capability,
        "allowed": _perms.can_access(agent_id, capability),
    }


@router.get("/agents")
async def list_agents():
    agents = _auth.list_agents()
    for a in agents:
        a["capabilities"] = _perms.get_capabilities(a["agent_id"])
    return {"agents": agents, "total": len(agents)}
