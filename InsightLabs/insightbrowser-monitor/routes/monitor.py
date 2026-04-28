"""
监控路由
"""
from fastapi import APIRouter
from typing import Optional
from services.monitor import _monitor

router = APIRouter(prefix="/api/v1/monitor", tags=["Monitor"])


@router.get("/check")
async def check_now():
    """立即执行一次全量健康检查"""
    return {"success": True, ** _monitor.check_all()}


@router.get("/history")
async def history(service: Optional[str] = None, limit: int = 20):
    return {"success": True, ** _monitor.history(service, limit)}


@router.get("/alerts")
async def alerts(limit: int = 20):
    return {"alerts": _monitor.alerts(limit), "count": len(_monitor._alerts)}


@router.get("/stats")
async def stats():
    return {"success": True, ** _monitor.stats()}


@router.get("/dashboard", summary="快速仪表盘")
async def dashboard():
    """一目了然的健康仪表盘"""
    health = _monitor.check_all()
    alerts = _monitor.alerts(5)
    return {
        "health": health,
        "recent_alerts": alerts,
        "uptime": _monitor.stats(),
    }
