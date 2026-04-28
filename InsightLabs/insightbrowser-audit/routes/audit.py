"""
审计路由
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from services.audit import get_audit

router = APIRouter(prefix="/api/v1/audit", tags=["Audit"])

_audit = get_audit()


class AuditRecordRequest(BaseModel):
    event_type: str = Field(..., description="task_start|task_end|payment|auth|dispute")
    agent_id: str
    target: str = ""
    action: str = ""
    data: dict = Field(default_factory=dict)
    result: str = "success"


class DisputeRequest(BaseModel):
    task_id: str
    claimant: str
    reason: str


@router.post("/record")
async def record(req: AuditRecordRequest):
    entry = _audit.record(req.event_type, req.agent_id, req.target, req.action, req.data, req.result)
    return {"success": True, "entry": entry}


@router.get("/query")
async def query(agent_id: Optional[str] = None, event_type: Optional[str] = None, limit: int = 50):
    return {"success": True, ** _audit.query(agent_id, event_type, limit)}


@router.get("/chain/{task_id}")
async def chain(task_id: str):
    return {"success": True, ** _audit.get_chain(task_id)}


@router.post("/dispute")
async def dispute(req: DisputeRequest):
    return {"success": True, ** _audit.dispute(req.task_id, req.claimant, req.reason)}


@router.get("/violations")
async def violations(agent_id: Optional[str] = None):
    return {"success": True, "violations": _audit.violations(agent_id)}


@router.get("/summary")
async def summary():
    return {"success": True, ** _audit.summary()}
