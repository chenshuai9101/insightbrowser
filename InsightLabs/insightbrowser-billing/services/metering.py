"""
计量引擎 — Agent 调用的资源消耗计量与费用计算
"""
import json
import os
from typing import Dict, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

PRICE_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "price_config.json")

DEFAULT_PRICE_CONFIG = {
    "base_price_per_call": 0.01,
    "price_per_second": 0.001,
    "price_per_1k_tokens": 0.02,
    "complexity_multiplier": {"1": 0.5, "2": 0.7, "3": 1.0, "4": 1.5, "5": 3.0},
    "currency": "CNY",
}

@dataclass
class UsageRecord:
    agent_id: str
    task_id: str
    execution_time_ms: float
    tokens_used: int
    data_transferred_bytes: int
    capability: str
    complexity: int = 3
    success: bool = True
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class MeteringEngine:
    def __init__(self):
        self.price_config = self._load_config()
        self._records: list = []

    def _load_config(self) -> dict:
        try:
            with open(PRICE_CONFIG_PATH) as f:
                return json.load(f)
        except:
            return dict(DEFAULT_PRICE_CONFIG)

    def _save_config(self):
        with open(PRICE_CONFIG_PATH, "w") as f:
            json.dump(self.price_config, f, indent=2)

    def calculate_cost(self, record: UsageRecord) -> float:
        """计算一次 Agent 调用的费用"""
        cfg = self.price_config
        base = cfg["base_price_per_call"]
        time_cost = (record.execution_time_ms / 1000) * cfg["price_per_second"]
        token_cost = (record.tokens_used / 1000) * cfg["price_per_1k_tokens"]
        multiplier = cfg["complexity_multiplier"].get(str(record.complexity), 1.0)
        cost = (base + time_cost + token_cost) * multiplier
        return round(cost, 4)

    def record_usage(self, usage: UsageRecord) -> dict:
        cost = self.calculate_cost(usage)
        record = {**asdict(usage), "cost": cost}
        self._records.append(record)
        return {"record": record, "cost": cost}

    def agent_usage(self, agent_id: str, last_n: int = 50) -> dict:
        records = [r for r in self._records if r.get("agent_id") == agent_id][-last_n:]
        total_cost = sum(r.get("cost", 0) for r in records)
        total_calls = len(records)
        total_tokens = sum(r.get("tokens_used", 0) for r in records)
        return {
            "agent_id": agent_id,
            "total_calls": total_calls,
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "recent_records": records[-20:],
        }

    def get_price_config(self) -> dict:
        return dict(self.price_config)

    def update_price_config(self, updates: dict) -> dict:
        for k, v in updates.items():
            if k in self.price_config:
                self.price_config[k] = v
        self._save_config()
        return self.price_config

    def all_records(self) -> list:
        return self._records[-100:]

    def stats(self) -> dict:
        records = self._records
        if not records:
            return {"total_calls": 0, "total_revenue": 0}
        return {
            "total_calls": len(records),
            "total_revenue": round(sum(r.get("cost", 0) for r in records), 4),
            "avg_cost": round(sum(r.get("cost", 0) for r in records) / len(records), 4),
            "avg_tokens": round(sum(r.get("tokens_used", 0) for r in records) / len(records), 1),
            "avg_latency_ms": round(sum(r.get("execution_time_ms", 0) for r in records) / len(records), 1),
        }


_metering = MeteringEngine()

def get_metering() -> MeteringEngine:
    return _metering
