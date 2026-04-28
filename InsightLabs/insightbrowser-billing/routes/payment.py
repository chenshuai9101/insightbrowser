"""
支付路由
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from services.payment import get_escrow

router = APIRouter(prefix="/api/v1/billing/escrow", tags=["Escrow"])

_escrow = get_escrow()


class DepositRequest(BaseModel):
    agent_id: str
    amount: float
    source: str = "deposit"


class HoldRequest(BaseModel):
    from_agent: str
    to_agent: str
    amount: float
    task_id: str


class ReleaseRequest(BaseModel):
    task_id: str


class RefundRequest(BaseModel):
    task_id: str
    reason: str = ""


@router.post("/deposit")
async def deposit(req: DepositRequest):
    return _escrow.deposit(req.agent_id, req.amount, req.source)


@router.post("/hold")
async def hold(req: HoldRequest):
    return _escrow.hold(req.from_agent, req.to_agent, req.amount, req.task_id)


@router.post("/release")
async def release(req: ReleaseRequest):
    return _escrow.release(req.task_id)


@router.post("/refund")
async def refund(req: RefundRequest):
    return _escrow.refund(req.task_id, req.reason)


@router.get("/balance/{agent_id}")
async def balance(agent_id: str):
    return _escrow.balance(agent_id)


@router.get("/holds")
async def list_holds():
    holds = _escrow.all_holds()
    return {"holds": holds, "count": len(holds)}
