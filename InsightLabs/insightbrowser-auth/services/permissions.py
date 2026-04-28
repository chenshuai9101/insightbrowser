"""
权限管理 — 能力级别的访问控制
"""
from typing import Dict, List, Set

# agent_id → [capabilities]
_capabilities: Dict[str, Set[str]] = {}


class PermissionManager:
    def grant(self, agent_id: str, capability: str) -> dict:
        if agent_id not in _capabilities:
            _capabilities[agent_id] = set()
        _capabilities[agent_id].add(capability)
        return {"success": True, "agent_id": agent_id, "granted": capability}

    def revoke(self, agent_id: str, capability: str) -> dict:
        if agent_id in _capabilities and capability in _capabilities[agent_id]:
            _capabilities[agent_id].discard(capability)
            return {"success": True, "agent_id": agent_id, "revoked": capability}
        return {"success": False, "error": "Capability not found"}

    def can_access(self, agent_id: str, capability: str) -> bool:
        if agent_id not in _capabilities:
            return False
        if "*" in _capabilities[agent_id]:
            return True
        return capability in _capabilities[agent_id]

    def get_capabilities(self, agent_id: str) -> List[str]:
        return sorted(list(_capabilities.get(agent_id, set())))

    def grant_all(self, agent_id: str) -> dict:
        _capabilities[agent_id] = {"*"}
        return {"success": True, "agent_id": agent_id, "granted": "*"}


_perms = PermissionManager()

def get_perms() -> PermissionManager:
    return _perms
