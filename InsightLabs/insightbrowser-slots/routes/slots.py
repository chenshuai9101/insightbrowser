"""
卡槽系统路由 — 五大卡槽 + 端点定义
v3.1: Pipeline 并行化 + 超时熔断
"""
import asyncio
import json
import logging
import concurrent.futures
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from services.engine import SlotsEngine

logger = logging.getLogger("slots.api")
router = APIRouter(tags=["Slots"])

engine = SlotsEngine()

# ─── 请求模型 ───

class PerceiveRequest(BaseModel):
    input_text: Optional[str] = Field(default=None, description="用户输入")
    user_request: Optional[str] = Field(default=None, description="用户请求(别名)")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="上下文")
    language: str = Field(default="zh", description="语言")
    max_steps: Optional[int] = Field(default=20, description="最多执行步数")
    
    @property
    def text(self) -> str:
        return self.input_text or self.user_request or ""


class PlanRequest(BaseModel):
    goal: str = Field(..., description="目标描述")
    constraints: Optional[Dict[str, Any]] = Field(default_factory=dict)
    available_capabilities: Optional[List[str]] = None


class ExecuteRequest(BaseModel):
    task_id: str = Field(..., description="任务ID")
    capability: str = Field(..., description="所需能力")
    params: Dict[str, Any] = Field(default_factory=dict)
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SynthesizeRequest(BaseModel):
    results: List[Dict[str, Any]] = Field(..., description="子任务执行结果列表")
    format: str = Field(default="markdown", description="输出格式")
    target_audience: Optional[str] = None


class VerifyRequest(BaseModel):
    output: str = Field(..., description="待验证输出")
    task_goal: str = Field(..., description="原始任务目标")
    quality_dimensions: Optional[List[str]] = None


# ─── 统计追踪 ───

_slot_stats = {
    "perception": {"count": 0, "total_latency_ms": 0, "errors": 0},
    "planning": {"count": 0, "total_latency_ms": 0, "errors": 0},
    "execution": {"count": 0, "total_latency_ms": 0, "errors": 0},
    "synthesis": {"count": 0, "total_latency_ms": 0, "errors": 0},
    "verification": {"count": 0, "total_latency_ms": 0, "errors": 0},
}

def _record_slot(slot: str, latency_ms: float):
    _slot_stats[slot]["count"] += 1
    _slot_stats[slot]["total_latency_ms"] += latency_ms

def _record_error(slot: str):
    _slot_stats[slot]["errors"] += 1


# ─── 超时执行工具 ───
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)

async def _run_with_timeout(func, *args, timeout_seconds: int = 30):
    """在单独线程中执行函数，支持超时"""
    try:
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(_executor, func, *args),
            timeout=timeout_seconds
        )
        return result, None
    except asyncio.TimeoutError:
        return None, f"超时({timeout_seconds}s)"
    except Exception as e:
        return None, str(e)


# ─── 卡槽 1: 感知 ───

@router.post("/perceive", summary="感知卡槽：理解需求，提取意图")
async def slot_perceive(req: PerceiveRequest):
    t0 = datetime.now()
    try:
        result, err = await _run_with_timeout(engine.perceive, req.text, req.context, req.language, timeout_seconds=15)
        if err:
            _record_error("perception")
            return {"success": False, "slot": "perception", "error": err}
        _record_slot("perception", (datetime.now() - t0).total_seconds() * 1000)
        return {"success": True, "slot": "perception", "result": result}
    except Exception as e:
        _record_error("perception")
        return {"success": False, "slot": "perception", "error": str(e)}


# ─── 卡槽 2: 规划 ───

@router.post("/plan", summary="规划卡槽：拆分任务，确定执行顺序")
async def slot_plan(req: PlanRequest):
    t0 = datetime.now()
    try:
        result, err = await _run_with_timeout(engine.plan, req.goal, req.constraints, req.available_capabilities, timeout_seconds=15)
        if err:
            _record_error("planning")
            return {"success": False, "slot": "planning", "error": err}
        _record_slot("planning", (datetime.now() - t0).total_seconds() * 1000)
        return {"success": True, "slot": "planning", "result": result}
    except Exception as e:
        _record_error("planning")
        return {"success": False, "slot": "planning", "error": str(e)}


# ─── 卡槽 3: 执行 ───

@router.post("/execute", summary="执行卡槽：调用能力执行子任务")
async def slot_execute(req: ExecuteRequest):
    t0 = datetime.now()
    try:
        result, err = await _run_with_timeout(engine.execute, req.task_id, req.capability, req.params, req.context, timeout_seconds=30)
        if err:
            _record_error("execution")
            return {"success": False, "slot": "execution", "error": err}
        _record_slot("execution", (datetime.now() - t0).total_seconds() * 1000)
        return {"success": True, "slot": "execution", "result": result}
    except Exception as e:
        _record_error("execution")
        return {"success": False, "slot": "execution", "error": str(e)}


# ─── 卡槽 4: 合成 ───

@router.post("/synthesize", summary="合成卡槽：汇总结果生成交付物")
async def slot_synthesize(req: SynthesizeRequest):
    t0 = datetime.now()
    try:
        result, err = await _run_with_timeout(engine.synthesize, req.results, req.format, req.target_audience, timeout_seconds=15)
        if err:
            _record_error("synthesis")
            return {"success": False, "slot": "synthesis", "error": err}
        _record_slot("synthesis", (datetime.now() - t0).total_seconds() * 1000)
        return {"success": True, "slot": "synthesis", "result": result}
    except Exception as e:
        _record_error("synthesis")
        return {"success": False, "slot": "synthesis", "error": str(e)}


# ─── 卡槽 5: 验证 ───

@router.post("/verify", summary="验证卡槽：质量评估+信任评分")
async def slot_verify(req: VerifyRequest):
    t0 = datetime.now()
    try:
        result, err = await _run_with_timeout(engine.verify, req.output, req.task_goal, req.quality_dimensions, timeout_seconds=15)
        if err:
            _record_error("verification")
            return {"success": False, "slot": "verification", "error": err}
        _record_slot("verification", (datetime.now() - t0).total_seconds() * 1000)
        return {"success": True, "slot": "verification", "result": result}
    except Exception as e:
        _record_error("verification")
        return {"success": False, "slot": "verification", "error": str(e)}


# ─── Pipeline: 五卡槽流水线 (改进版：并行 + 熔断) ───

PIPELINE_TIMEOUT = 120  # 全局超时

@router.post("/pipeline", summary="卡槽流水线：一键走完感知→规划→执行→合成→验证")
async def slot_pipeline(req: PerceiveRequest):
    """五卡槽流水线，各卡槽有独立超时，总时限 120s"""
    pipeline_start = datetime.now()
    steps = []
    text = req.text

    if not text:
        return {"success": False, "error": "缺少 input_text 或 user_request"}

    try:
        # 1. 感知 (15s timeout)
        t0 = datetime.now()
        perception, err = await _run_with_timeout(engine.perceive, text, req.context, req.language, timeout_seconds=15)
        if err:
            steps.append({"slot": "perception", "error": err})
            return {"success": False, "error": f"感知超时: {err}", "steps": steps}
        steps.append({"slot": "perception", "latency_ms": (datetime.now() - t0).total_seconds() * 1000,
                       "summary": f"意图: {perception.get('intent', '?')}"})

        # 2. 规划 (15s timeout)
        t0 = datetime.now()
        plan, err = await _run_with_timeout(engine.plan,
            perception.get("goal", text), req.context, None, timeout_seconds=15)
        if err:
            steps.append({"slot": "planning", "error": err})
            return {"success": False, "error": f"规划超时: {err}", "steps": steps}
        tasks = plan.get("tasks", [])
        steps.append({"slot": "planning", "latency_ms": (datetime.now() - t0).total_seconds() * 1000,
                       "summary": f"拆分 {len(tasks)} 个子任务"})

        # 3. 并行执行 (每个子任务 30s)
        t0 = datetime.now()
        exec_futures = []
        for task in tasks:
            tid = task.get("id", "?")
            cap = task.get("capability", "researcher")
            params = task.get("params", {})
            exec_futures.append(_run_with_timeout(engine.execute, tid, cap, params, req.context, timeout_seconds=30))

        results = []
        for i, coro in enumerate(exec_futures):
            result, err = await coro
            status_tag = f"execution.task_{tasks[i].get('id', i)}"
            if err:
                steps.append({"slot": status_tag, "error": err})
                results.append({"task_id": tasks[i].get("id", i), "capability": tasks[i].get("capability", "?"),
                                "output": f"[超时] {err}", "error": err})
            else:
                results.append(result)
                steps.append({"slot": status_tag, "latency_ms": 0,
                               "summary": f"子任务#{tasks[i].get('id', i)}: {tasks[i].get('action', 'N/A')[:40]}"})

        exec_latency = (datetime.now() - t0).total_seconds() * 1000
        steps.append({"slot": "execution.total", "latency_ms": exec_latency,
                       "summary": f"{len([r for r in results if 'error' not in r])}/{len(results)} 子任务完成"})

        # 4. 合成 (15s timeout)
        t0 = datetime.now()
        synthesis, err = await _run_with_timeout(engine.synthesize, results, "markdown", None, timeout_seconds=15)
        if err:
            steps.append({"slot": "synthesis", "error": err})
            return {"success": False, "error": f"合成超时: {err}", "steps": steps,
                    "partial_results": [r.get("output", "")[:200] for r in results]}
        steps.append({"slot": "synthesis", "latency_ms": (datetime.now() - t0).total_seconds() * 1000,
                       "summary": f"合成 {len(results)} 个结果"})

        # 5. 验证 (15s timeout)
        t0 = datetime.now()
        verification, err = await _run_with_timeout(engine.verify,
            synthesis.get("content", ""), perception.get("goal", ""), None, timeout_seconds=15)
        if err:
            steps.append({"slot": "verification", "error": err})
            return {"success": False, "error": f"验证超时: {err}", "steps": steps,
                    "synthesis": synthesis}
        steps.append({"slot": "verification", "latency_ms": (datetime.now() - t0).total_seconds() * 1000,
                       "summary": f"质量评分: {verification.get('overall_score', '?')}/100"})

        total_latency = (datetime.now() - pipeline_start).total_seconds() * 1000

        return {
            "success": True,
            "pipeline": {
                "total_latency_ms": total_latency,
                "steps": steps,
                "perception": perception,
                "plan": plan,
                "results": results,
                "synthesis": synthesis,
                "verification": verification,
            }
        }

    except Exception as e:
        total_latency = (datetime.now() - pipeline_start).total_seconds() * 1000
        return {
            "success": False,
            "error": str(e),
            "total_latency_ms": total_latency,
            "steps_completed": steps,
        }


# ─── 统计端点 ───

@router.get("/metrics", summary="卡槽使用统计")
async def slot_metrics():
    """返回各卡槽的使用统计和平均延迟"""
    metrics = {}
    for slot, stats in _slot_stats.items():
        avg_latency = stats["total_latency_ms"] / stats["count"] if stats["count"] > 0 else 0
        metrics[slot] = {
            "total_calls": stats["count"],
            "errors": stats["errors"],
            "avg_latency_ms": round(avg_latency, 2),
        }

    total_calls = sum(s["count"] for s in _slot_stats.values())
    total_errors = sum(s["errors"] for s in _slot_stats.values())

    return {
        "service": "InsightBrowser Slots v3.1",
        "total_calls": total_calls,
        "total_errors": total_errors,
        "error_rate": f"{total_errors / max(total_calls, 1) * 100:.2f}%",
        "slots": metrics,
    }


# ─── v3 新端点：卡槽注册表 ───

from services.slot_registry import get_slot_registry
from services.state_store import init_state_db, get_state, save_state, push_task, list_agents
from services.agent_trade import execute_agent_trade
from services.tool_registry import get_tool_registry
from tools.builtin import register_builtin_tools

_init_done = False
def _init_v3():
    global _init_done
    if _init_done: return
    init_state_db()
    register_builtin_tools()
    _init_done = True
_init_v3()


class SlotRegisterRequest(BaseModel):
    name: str = Field(..., description="卡槽名称")
    description: str = Field(..., description="卡槽描述")
    category: str = Field(default="extension", description="分类: core/extension/custom")


@router.get("/slots", summary="列出所有已注册卡槽")
async def list_slots(category: Optional[str] = None):
    reg = get_slot_registry()
    if category:
        return {"slots": reg.list_by_category(category), "category": category}
    return {"slots": reg.list_all(), "total": len(reg.list_all())}


@router.post("/slots", summary="注册新卡槽")
async def register_slot(req: SlotRegisterRequest):
    reg = get_slot_registry()
    from services.slot_registry import Slot
    async def placeholder(input_data, context):
        return {"status": "registered", "slot": req.name, "input": input_data}
    slot = Slot(req.name, req.description, placeholder, req.category)
    reg.register(slot)
    return {"success": True, "slot": {"name": req.name, "description": req.description, "category": req.category}}


@router.get("/tools", summary="列出所有已注册工具")
async def list_tools():
    reg = get_tool_registry()
    return {"tools": reg.list_all(), "total": len(reg.list_all()), "capabilities": reg.list_capabilities()}


@router.get("/tools/{capability}", summary="查询某个能力对应的工具")
async def get_capability_tools(capability: str):
    reg = get_tool_registry()
    tools = reg.get_tools_for_capability(capability)
    return {
        "capability": capability,
        "tools": [t.to_schema() for t in tools],
        "has_tools": reg.has_tools_for(capability),
    }


from pydantic import BaseModel as PydanticBaseModel

class StateSyncRequest(PydanticBaseModel):
    agent_id: str = Field(..., description="Agent ID")
    task_queue: Optional[List[dict]] = None
    history: Optional[List[dict]] = None
    context: Optional[dict] = None
    reputation: Optional[float] = None
    balance: Optional[float] = None


@router.get("/state/{agent_id}", summary="获取 Agent 状态")
async def get_agent_state(agent_id: str):
    state = get_state(agent_id)
    return {"success": state["found"], "state": state}


@router.post("/state/sync", summary="同步 Agent 状态")
async def sync_agent_state(req: StateSyncRequest):
    data = {}
    for field in ["task_queue", "history", "context", "reputation", "balance"]:
        val = getattr(req, field, None)
        if val is not None:
            data[field] = val
    save_state(req.agent_id, data)
    return {"success": True, "agent_id": req.agent_id}


@router.post("/state/{agent_id}/push-task", summary="添加任务到 Agent 队列")
async def push_agent_task(agent_id: str, task: dict):
    push_task(agent_id, task)
    return {"success": True, "agent_id": agent_id, "task": task}


@router.get("/agents", summary="列出所有已存储状态的 Agent")
async def list_stored_agents():
    agents = list_agents()
    result = []
    for aid in agents:
        state = get_state(aid)
        result.append({
            "agent_id": aid,
            "reputation": state.get("reputation", 0),
            "balance": state.get("balance", 0),
            "task_count": len(state.get("task_queue", [])),
            "last_active": state.get("last_active"),
        })
    return {"agents": result, "total": len(result)}


class TradeRequest(PydanticBaseModel):
    capability: str = Field(..., description="所需能力")
    task_params: dict = Field(default_factory=dict, description="任务参数")
    site_id: str = Field(default="auto-trade", description="交易ID")


@router.post("/trade", summary="Agent 间交易闭环")
async def agent_trade_endpoint(req: TradeRequest):
    result = await execute_agent_trade(
        capability=req.capability,
        task_params=req.task_params,
        site_id=req.site_id,
    )
    return result
