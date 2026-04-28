"""
支付与托管服务 — 资金托管、放款、退款
"""
import logging
import requests
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger("payment")

RELIABILITY_URL = "http://localhost:7003/api/ledger/record"
SLOTS_STATE_URL = "http://localhost:7005/api/v1/slots/state/sync"


class EscrowManager:
    """资金托管管理器"""

    def __init__(self):
        # agent_id → balance (可用余额)
        self._balances: Dict[str, float] = {}
        # task_id → {from, to, amount, status}
        self._holds: Dict[str, dict] = {}

    def deposit(self, agent_id: str, amount: float, source: str = "deposit") -> dict:
        if agent_id not in self._balances:
            self._balances[agent_id] = 0.0
        self._balances[agent_id] += amount
        self._sync_to_ledger("system", agent_id, f"deposit:{source}", amount, True)
        return {"success": True, "agent_id": agent_id, "balance": self._balances[agent_id]}

    def hold(self, from_agent: str, to_agent: str, amount: float, task_id: str) -> dict:
        if from_agent not in self._balances or self._balances[from_agent] < amount:
            return {"success": False, "error": f"Insufficient balance: {self._balances.get(from_agent, 0)} < {amount}"}
        self._balances[from_agent] -= amount
        self._holds[task_id] = {
            "from": from_agent,
            "to": to_agent,
            "amount": amount,
            "status": "held",
            "created_at": datetime.now().isoformat(),
        }
        self._sync_to_ledger(from_agent, to_agent, f"hold:{task_id}", amount, True)
        return {"success": True, "task_id": task_id, "held": amount}

    def release(self, task_id: str) -> dict:
        if task_id not in self._holds:
            return {"success": False, "error": "Hold not found"}
        h = self._holds[task_id]
        if h["status"] != "held":
            return {"success": False, "error": f"Already {h['status']}"}
        if h["to"] not in self._balances:
            self._balances[h["to"]] = 0.0
        self._balances[h["to"]] += h["amount"]
        h["status"] = "released"
        h["released_at"] = datetime.now().isoformat()
        self._sync_to_ledger(h["from"], h["to"], f"release:{task_id}", h["amount"], True)
        self._sync_slots_balance(h["from"])
        self._sync_slots_balance(h["to"])
        return {"success": True, "task_id": task_id, "to": h["to"], "amount": h["amount"]}

    def refund(self, task_id: str, reason: str = "") -> dict:
        if task_id not in self._holds:
            return {"success": False, "error": "Hold not found"}
        h = self._holds[task_id]
        if h["status"] != "held":
            return {"success": False, "error": f"Already {h['status']}"}
        self._balances[h["from"]] += h["amount"]
        h["status"] = "refunded"
        h["refund_reason"] = reason
        h["refunded_at"] = datetime.now().isoformat()
        self._sync_to_ledger(h["to"], h["from"], f"refund:{task_id}", h["amount"], False)
        self._sync_slots_balance(h["from"])
        return {"success": True, "task_id": task_id, "refunded": h["amount"], "reason": reason}

    def balance(self, agent_id: str) -> dict:
        return {"agent_id": agent_id, "balance": self._balances.get(agent_id, 0.0)}

    def all_holds(self) -> list:
        return [{"task_id": k, **v} for k, v in self._holds.items()]

    def _sync_to_ledger(self, from_a: str, to_a: str, action: str, amount: float, success: bool):
        try:
            requests.post(RELIABILITY_URL, json={
                "from_agent": from_a,
                "to_agent": to_a,
                "site_id": f"billing-{action}",
                "action": action,
                "tokens_used": int(amount * 1000),
                "success": success,
            }, timeout=5)
        except Exception as e:
            logger.warning(f"Ledger sync failed: {e}")

    def _sync_slots_balance(self, agent_id: str):
        try:
            requests.post(SLOTS_STATE_URL, json={
                "agent_id": agent_id,
                "balance": self._balances.get(agent_id, 0.0),
            }, timeout=5)
        except Exception as e:
            logger.warning(f"Slots state sync failed: {e}")


_escrow = EscrowManager()

def get_escrow() -> EscrowManager:
    return _escrow
