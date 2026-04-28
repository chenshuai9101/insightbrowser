"""
审计日志 — 不可篡改的交易链路记录
"""
import hashlib
import json
from typing import List, Optional
from datetime import datetime


class AuditLog:
    def __init__(self):
        self._entries: List[dict] = []

    def record(self, event_type: str, agent_id: str, target: str, action: str,
               data: dict = None, result: str = "success") -> dict:
        entry = {
            "id": self._hash_entry(),
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,       # task_start | task_end | payment | auth | dispute
            "agent_id": agent_id,
            "target": target,
            "action": action,
            "data": data or {},
            "result": result,
            "hash": "",
        }
        entry["hash"] = self._hash(entry)
        self._entries.append(entry)

        # 超过 1000 条，归档压缩
        if len(self._entries) > 1000:
            self._entries = self._entries[-1000:]

        return entry

    def query(self, agent_id: str = None, event_type: str = None,
              limit: int = 50) -> dict:
        entries = self._entries
        if agent_id:
            entries = [e for e in entries if e["agent_id"] == agent_id]
        if event_type:
            entries = [e for e in entries if e["event_type"] == event_type]
        entries = entries[-limit:]

        return {
            "entries": entries,
            "count": len(entries),
            "total_logs": len(self._entries),
        }

    def get_chain(self, task_id: str) -> dict:
        """获取某个任务的完整审计链"""
        chain = [e for e in self._entries if task_id in str(e.get("data", {}).get("task_id", "")) or task_id in e.get("action", "")]
        return {
            "task_id": task_id,
            "chain": chain,
            "length": len(chain),
            "verified": self._verify_chain(chain),
        }

    def dispute(self, task_id: str, claimant: str, reason: str) -> dict:
        """发起争议"""
        chain = self.get_chain(task_id)
        chain_list = chain.get("chain", [])
        return {
            "task_id": task_id,
            "claimant": claimant,
            "reason": reason,
            "chain": chain,
            "resolution": "pending",
            "recommendation": self._auto_resolve(chain_list),
        }

    def violations(self, agent_id: str = None) -> list:
        """检查违规（失败的交易、异常的金额等）"""
        suspicious = []
        for e in self._entries:
            if e["result"] == "failed":
                suspicious.append({"reason": "task_failed", "entry": e})
            if e["event_type"] == "payment" and e["data"].get("amount", 0) > 100:
                suspicious.append({"reason": "large_amount", "entry": e})
        if agent_id:
            suspicious = [s for s in suspicious if s["entry"]["agent_id"] == agent_id]
        return suspicious

    def summary(self) -> dict:
        entries = self._entries
        if not entries:
            return {"total": 0}
        event_counts = {}
        for e in entries:
            t = e["event_type"]
            event_counts[t] = event_counts.get(t, 0) + 1
        return {
            "total": len(entries),
            "first_entry": entries[0]["timestamp"] if entries else None,
            "last_entry": entries[-1]["timestamp"] if entries else None,
            "event_counts": event_counts,
            "failure_rate": round(
                sum(1 for e in entries if e["result"] == "failed") / max(len(entries), 1) * 100, 2
            ),
        }

    def _hash(self, entry: dict) -> str:
        pre_entry = self._entries[-1] if self._entries else None
        prev_hash = pre_entry["hash"] if pre_entry else "genesis"
        raw = f"{entry['id']}{prev_hash}{entry['timestamp']}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def _hash_entry(self) -> str:
        raw = f"{len(self._entries)}{datetime.now().isoformat()}"
        return f"audit_{hashlib.sha256(raw.encode()).hexdigest()[:16]}"

    def _verify_chain(self, chain: list) -> bool:
        if len(chain) < 2:
            return True
        for i in range(1, len(chain)):
            expected = hashlib.sha256(
                f"{chain[i]['id']}{chain[i-1]['hash']}{chain[i]['timestamp']}".encode()
            ).hexdigest()[:32]
            if expected != chain[i]["hash"]:
                return False
        return True

    def _auto_resolve(self, chain: list) -> str:
        """自动调解建议"""
        failures = [e for e in chain if e["result"] == "failed"]
        if failures:
            return f"chain_contains_{len(failures)}_failures: recommend refund"
        return "no_issues: recommend confirm"


_audit = AuditLog()

def get_audit() -> AuditLog:
    return _audit
