import json, time, heapq
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["failover"])

class FailoverRequest(BaseModel):
    target_id: str
    context: str = "general"  # finance/ecommerce/creative
    max_latency_ms: float = 5000.0

class FailoverCandidate(BaseModel):
    id: str
    name: str
    rating: str
    uptime: float
    estimated_latency_ms: float
    score: float

class FailoverResponse(BaseModel):
    primary_id: str
    primary_healthy: bool
    failover_to: Optional[FailoverCandidate]
    candidates: List[FailoverCandidate]
    reason: str
    timestamp: float

# In-memory health state (synced with Reliability heartbeat)
_health_state: Dict[str, Dict[str, Any]] = {}
_last_sync: float = 0

def _get_healthy_sites():
    """Fetch current healthy sites from Reliability service"""
    global _health_state, _last_sync
    now = time.time()
    if now - _last_sync < 5:  # 5s cache
        return _health_state

    try:
        import urllib.request
        req = urllib.request.Request(
            "http://localhost:7003/api/reliability/report?limit=50",
            headers={"User-Agent": "InsightBrowser/1.0"},
            timeout=3
        )
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())
            sites = data.get("sites", data.get("data", []))
            for site in sites:
                sid = site.get("site_id", site.get("id", ""))
                _health_state[sid] = {
                    "id": sid,
                    "name": site.get("name", sid),
                    "rating": site.get("rating", "C"),
                    "uptime": site.get("up_time", site.get("uptime", 0)),
                    "healthy": site.get("status", "").lower() == "healthy",
                }
            _last_sync = now
    except Exception as e:
        pass  # 返回缓存的旧状态

    return _health_state

def _calculate_score(site: Dict[str, Any], context: str, max_latency_ms: float) -> float:
    """情境化评分：金融偏安全，创意偏速度，电商偏成功率"""
    rating_weights = {"S": 1.0, "A": 0.85, "B": 0.65, "C": 0.4, "D": 0.1}
    rating_weight = rating_weights.get(site.get("rating", "C"), 0.4)
    uptime = site.get("uptime", 0.5)

    if context == "finance":
        # 安全性权重最高
        score = rating_weight * 0.6 + uptime * 0.3 + 0.1
    elif context == "creative":
        # 响应速度优先
        speed = min(1.0, max_latency_ms / (site.get("estimated_latency_ms", 500) + 1))
        score = speed * 0.4 + rating_weight * 0.3 + uptime * 0.3
    elif context == "ecommerce":
        # 成功率优先
        score = uptime * 0.5 + rating_weight * 0.3 + 0.2
    else:
        score = rating_weight * 0.4 + uptime * 0.4 + 0.2

    return score

@router.post("/failover", response_model=FailoverResponse)
async def failover(req: FailoverRequest):
    """信誉路由漂移 — 发现主目标健康时自动推荐替代"""
    sites = _get_healthy_sites()

    # 检查主目标
    primary = sites.get(req.target_id)
    primary_healthy = primary.get("healthy", False) if primary else False

    # 筛选健康候选
    candidates = []
    for site_id, site in sites.items():
        if site_id == req.target_id:
            continue
        if not site.get("healthy", False):
            continue
        score = _calculate_score(site, req.context, req.max_latency_ms)
        candidates.append({
            "id": site_id,
            "name": site.get("name", site_id),
            "rating": site.get("rating", "C"),
            "uptime": site.get("uptime", 0),
            "estimated_latency_ms": int((1 - site.get("uptime", 0.5)) * 1000),
            "score": round(score, 3),
        })

    # 按评分降序
    candidates.sort(key=lambda x: x["score"], reverse=True)

    failover_to = None
    reason = ""

    if not primary:
        reason = "主目标不存在"
        if candidates:
            failover_to = candidates[0]
    elif not primary_healthy:
        reason = "主目标健康检查失败 → 自动漂移"
        if candidates:
            failover_to = candidates[0]
    else:
        reason = "主目标健康"

    return FailoverResponse(
        primary_id=req.target_id,
        primary_healthy=primary_healthy,
        failover_to=failover_to,
        candidates=candidates[:5],
        reason=reason,
        timestamp=time.time(),
    )

@router.get("/failover/health")
async def failover_health():
    """检查 failover 子系统健康"""
    return {
        "status": "healthy",
        "cached_sites": len(_health_state),
        "last_sync": _last_sync,
        "age_seconds": int(time.time() - _last_sync) if _last_sync else None,
    }

