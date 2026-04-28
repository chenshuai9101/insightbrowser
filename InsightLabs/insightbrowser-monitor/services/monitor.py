"""
InsightBrowser Monitor — 服务健康监控与告警
端口: 7010
"""
import asyncio
import time
from typing import Dict, List
from datetime import datetime
from dataclasses import dataclass, asdict

import requests

# 监控配置
WATCHED_SERVICES = {
    "registry": ("http://localhost:7000", 200),
    "hosting": ("http://localhost:7001", 200),
    "ahp": ("http://localhost:7002", 200),
    "reliability": ("http://localhost:7003", 200),
    "commerce": ("http://localhost:7004", 200),
    "slots": ("http://localhost:7005", 200),
    "billing": ("http://localhost:7006", 200),
    "auth": ("http://localhost:7007", 200),
    "queue": ("http://localhost:7008", 200),
    "insighthub": ("http://localhost:8080", 200),
    "insightsee": ("http://localhost:9090", 404),
}

@dataclass
class HealthRecord:
    service: str
    status: str  # "up" | "down" | "degraded"
    status_code: int
    latency_ms: float
    timestamp: str


class MonitorEngine:
    def __init__(self):
        self._history: Dict[str, List[HealthRecord]] = {svc: [] for svc in WATCHED_SERVICES}
        self._alerts: List[dict] = []
        self._started_at = datetime.now().isoformat()

    def check_all(self) -> dict:
        results = {}
        for service, (url, expected) in WATCHED_SERVICES.items():
            t0 = time.time()
            try:
                r = requests.get(url, timeout=5)
                code = r.status_code
                latency = (time.time() - t0) * 1000
                if code == expected or (expected == 404 and code == 404):
                    status = "up"
                else:
                    status = "degraded"
                    self._add_alert(service, f"Unexpected status: {code} (expected {expected})")
            except Exception as e:
                code = 0
                latency = (time.time() - t0) * 1000
                status = "down"
                self._add_alert(service, str(e))

            record = HealthRecord(service, status, code, round(latency, 1), datetime.now().isoformat())
            self._history[service].append(record)

            # 只保留最近 100 条
            if len(self._history[service]) > 100:
                self._history[service] = self._history[service][-100:]

            results[service] = {
                "status": status,
                "code": code,
                "latency_ms": round(latency, 1),
            }

        online = sum(1 for r in results.values() if r["status"] == "up")
        return {
            "checked_at": datetime.now().isoformat(),
            "online": online,
            "total": len(results),
            "all_healthy": online == len(results),
            "services": results,
        }

    def history(self, service: str = None, limit: int = 20) -> dict:
        if service:
            records = self._history.get(service, [])[-limit:]
            return {"service": service, "records": [asdict(r) for r in records]}
        return {
            svc: [asdict(r) for r in records[-limit:]]
            for svc, records in self._history.items()
        }

    def alerts(self, limit: int = 20) -> list:
        return self._alerts[-limit:]

    def stats(self) -> dict:
        total_downtime = 0
        total_checks = 0
        avg_latency = {}
        for svc, records in self._history.items():
            if records:
                downs = sum(1 for r in records if r.status == "down")
                avg_lat = sum(r.latency_ms for r in records) / len(records)
                avg_latency[svc] = round(avg_lat, 1)
                total_checks += len(records)
        return {
            "started_at": self._started_at,
            "total_checks": total_checks,
            "services_watched": len(WATCHED_SERVICES),
            "alerts_count": len(self._alerts),
            "avg_latency": avg_latency,
        }

    def _add_alert(self, service: str, detail: str):
        alert = {
            "service": service,
            "detail": detail,
            "time": datetime.now().isoformat(),
            "acknowledged": False,
        }
        # 去重：同一服务 60 秒内不重复告警
        recent = [a for a in self._alerts if a["service"] == service and not a.get("acknowledged")]
        if recent:
            last_time = datetime.fromisoformat(recent[-1]["time"])
            if (datetime.now() - last_time).total_seconds() < 60:
                return
        self._alerts.append(alert)


_monitor = MonitorEngine()


async def monitor_loop(interval: int = 30):
    """后台监控循环"""
    while True:
        _monitor.check_all()
        await asyncio.sleep(interval)
