"""
Agent 身份认证 — API Key 签发、验证、权限管理
"""
import hashlib
import secrets
import time
from typing import Dict, Optional
from datetime import datetime

# 内存存储 (可替换为数据库)
_agent_keys: Dict[str, dict] = {}  # agent_id → {api_key, secret, metadata, created_at}
_key_index: Dict[str, str] = {}    # api_key → agent_id


class AuthManager:
    def register(self, agent_id: str, metadata: dict = None) -> dict:
        if agent_id in _agent_keys:
            return {"success": False, "error": "Agent already registered"}
        secret = secrets.token_hex(16)
        api_key = self._generate_key(agent_id)
        _agent_keys[agent_id] = {
            "agent_id": agent_id,
            "api_key": api_key,
            "secret": secret,
            "metadata": metadata or {},
            "role": "agent",
            "created_at": datetime.now().isoformat(),
        }
        _key_index[api_key] = agent_id
        return {"success": True, "agent_id": agent_id, "api_key": api_key, "secret": secret}

    def verify(self, api_key: str) -> Optional[dict]:
        agent_id = _key_index.get(api_key)
        if agent_id and agent_id in _agent_keys:
            return dict(_agent_keys[agent_id])
        return None

    def verify_header(self, authorization: str) -> Optional[dict]:
        if not authorization:
            return None
        if authorization.startswith("Bearer "):
            return self.verify(authorization[7:])
        if authorization.startswith("X-Api-Key "):
            return self.verify(authorization[9:])
        return self.verify(authorization)

    def get_agent(self, agent_id: str) -> Optional[dict]:
        return _agent_keys.get(agent_id)

    def set_role(self, agent_id: str, role: str) -> bool:
        if agent_id in _agent_keys:
            _agent_keys[agent_id]["role"] = role
            return True
        return False

    def list_agents(self) -> list:
        return [
            {"agent_id": v["agent_id"], "role": v["role"], "created_at": v["created_at"]}
            for v in _agent_keys.values()
        ]

    def _generate_key(self, agent_id: str) -> str:
        raw = f"{agent_id}:{time.time()}:{secrets.token_hex(8)}"
        return f"ak_{hashlib.sha256(raw.encode()).hexdigest()[:32]}"


_auth = AuthManager()

def get_auth() -> AuthManager:
    return _auth
