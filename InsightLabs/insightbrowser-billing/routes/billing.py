"""
计费路由
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from services.metering import UsageRecord, get_metering

router = APIRouter(prefix="/api/v1/billing", tags=["Billing"])

_metering = get_metering()


class UsageRequest(BaseModel):
    agent_id: str
    task_id: str
    execution_time_ms: float
    tokens_used: int = 0
    data_transferred_bytes: int = 0
    capability: str = "unknown"
    complexity: int = 3
    success: bool = True


class PriceConfigUpdate(BaseModel):
    base_price_per_call: Optional[float] = None
    price_per_second: Optional[float] = None
    price_per_1k_tokens: Optional[float] = None


@router.post("/meter")
async def record_metering(req: UsageRequest):
    record = UsageRecord(
        agent_id=req.agent_id, task_id=req.task_id,
        execution_time_ms=req.execution_time_ms,
        tokens_used=req.tokens_used,
        data_transferred_bytes=req.data_transferred_bytes,
        capability=req.capability, complexity=req.complexity,
        success=req.success,
    )
    result = _metering.record_usage(record)
    return {"success": True, **result}


@router.get("/price-config")
async def get_price_config():
    return {"success": True, "config": _metering.get_price_config()}


@router.put("/price-config")
async def update_price_config(req: PriceConfigUpdate):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    cfg = _metering.update_price_config(updates)
    return {"success": True, "config": cfg}


@router.get("/usage/{agent_id}")
async def agent_usage(agent_id: str):
    return {"success": True, ** _metering.agent_usage(agent_id)}


@router.get("/stats")
async def billing_stats():
    return {"success": True, ** _metering.stats()}
