"""
卡槽系统路由 — 五大卡槽 + 端点定义
"""
import json
import logging
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
    input_text: str = Field(..., description="用户输入")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="上下文")
    language: str = Field(default="zh", description="语言")

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

# ─── 卡槽 1: 感知 ───

@router.post("/perceive", summary="感知卡槽：理解需求，提取意图")
async def slot_perceive(req: PerceiveRequest):
    """
    感知卡槽负责：
    - 解析用户输入的自然语言
    - 识别意图类型
    - 提取关键信息
    - 评估复杂度
    """
    t0 = datetime.now()
    try:
        result = engine.perceive(req.input_text, req.context, req.language)
        latency = (datetime.now() - t0).total_seconds() * 1000
        _record_slot("perception", latency)
        return {
            "success": True,
            "slot": "perception",
            "result": result,
            "metadata": {"latency_ms": latency}
        }
    except Exception as e:
        _record_error("perception")
        raise HTTPException(status_code=500, detail=str(e))

# ─── 卡槽 2: 规划 ───

@router.post("/plan", summary="规划卡槽：拆分任务，制定策略")
async def slot_plan(req: PlanRequest):
    """
    规划卡槽负责：
    - 将目标拆分为可执行子任务
    - 确定子任务依赖关系
    - 匹配所需能力
    - 制定执行顺序
    """
    t0 = datetime.now()
    try:
        result = engine.plan(req.goal, req.constraints, req.available_capabilities)
        latency = (datetime.now() - t0).total_seconds() * 1000
        _record_slot("planning", latency)
        return {
            "success": True,
            "slot": "planning",
            "result": result,
            "metadata": {"latency_ms": latency}
        }
    except Exception as e:
        _record_error("planning")
        raise HTTPException(status_code=500, detail=str(e))

# ─── 卡槽 3: 执行 ───

@router.post("/execute", summary="执行卡槽：调用能力，完成子任务")
async def slot_execute(req: ExecuteRequest):
    """
    执行卡槽负责：
    - 接收子任务描述
    - 匹配并调用合适的 Agent
    - 监控执行过程
    - 返回执行结果
    """
    t0 = datetime.now()
    try:
        result = engine.execute(req.task_id, req.capability, req.params, req.context)
        latency = (datetime.now() - t0).total_seconds() * 1000
        _record_slot("execution", latency)
        return {
            "success": True,
            "slot": "execution",
            "result": result,
            "metadata": {"latency_ms": latency}
        }
    except Exception as e:
        _record_error("execution")
        raise HTTPException(status_code=500, detail=str(e))

# ─── 卡槽 4: 合成 ───

@router.post("/synthesize", summary="合成卡槽：汇总结果，生成交付物")
async def slot_synthesize(req: SynthesizeRequest):
    """
    合成卡槽负责：
    - 汇总多个子任务的结果
    - 去重、去噪、结构化
    - 按指定格式组织输出
    - 生成最终交付物
    """
    t0 = datetime.now()
    try:
        result = engine.synthesize(req.results, req.format, req.target_audience)
        latency = (datetime.now() - t0).total_seconds() * 1000
        _record_slot("synthesis", latency)
        return {
            "success": True,
            "slot": "synthesis",
            "result": result,
            "metadata": {"latency_ms": latency}
        }
    except Exception as e:
        _record_error("synthesis")
        raise HTTPException(status_code=500, detail=str(e))

# ─── 卡槽 5: 验证 ───

@router.post("/verify", summary="验证卡槽：质量检查，信任更新")
async def slot_verify(req: VerifyRequest):
    """
    验证卡槽负责：
    - 检查交付物质量
    - 评估是否满足原始目标
    - 多维度打分（完整性、准确性、可读性、原创性）
    - 输出信任更新建议
    """
    t0 = datetime.now()
    try:
        result = engine.verify(req.output, req.task_goal, req.quality_dimensions)
        latency = (datetime.now() - t0).total_seconds() * 1000
        _record_slot("verification", latency)
        return {
            "success": True,
            "slot": "verification",
            "result": result,
            "metadata": {"latency_ms": latency}
        }
    except Exception as e:
        _record_error("verification")
        raise HTTPException(status_code=500, detail=str(e))

# ─── 流水线端点 ───

@router.post("/pipeline", summary="卡槽流水线：一键走完感知→规划→执行→合成→验证")
async def slot_pipeline(req: PerceiveRequest):
    """
    将五大卡槽串联成一条完整的流水线。
    输入一句话，输出验证后的完整交付物。
    """
    pipeline_start = datetime.now()
    steps = []

    try:
        # 1. 感知
        t0 = datetime.now()
        perception = engine.perceive(req.input_text, req.context, req.language)
        steps.append({
            "slot": "perception",
            "latency_ms": (datetime.now() - t0).total_seconds() * 1000,
            "summary": f"识别意图: {perception.get('intent', 'unknown')}"
        })

        # 2. 规划
        t0 = datetime.now()
        plan = engine.plan(perception.get("goal", req.input_text), req.context)
        steps.append({
            "slot": "planning",
            "latency_ms": (datetime.now() - t0).total_seconds() * 1000,
            "summary": f"拆分 {plan.get('total_tasks', 0)} 个子任务"
        })

        # 3. 执行（每个子任务）
        results = []
        for task in plan.get("tasks", []):
            t0 = datetime.now()
            result = engine.execute(task["id"], task["capability"], task.get("params", {}), req.context)
            results.append(result)
            steps.append({
                "slot": f"execution.task_{task['id']}",
                "latency_ms": (datetime.now() - t0).total_seconds() * 1000,
                "summary": f"执行子任务#{task['id']}: {task.get('action', 'N/A')[:40]}"
            })

        # 4. 合成
        t0 = datetime.now()
        synthesis = engine.synthesize(results, "markdown")
        steps.append({
            "slot": "synthesis",
            "latency_ms": (datetime.now() - t0).total_seconds() * 1000,
            "summary": f"合成 {len(results)} 个结果"
        })

        # 5. 验证
        t0 = datetime.now()
        verification = engine.verify(synthesis.get("content", ""), perception.get("goal", ""))
        steps.append({
            "slot": "verification",
            "latency_ms": (datetime.now() - t0).total_seconds() * 1000,
            "summary": f"质量评分: {verification.get('overall_score', 0)}/100"
        })

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
        return {
            "success": False,
            "error": str(e),
            "steps_completed": steps
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
        "service": "InsightBrowser Slots v3",
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

# 启动时初始化
_init_done = False

def _init_v3():
    global _init_done
    if _init_done:
        return
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
    # 新注册的卡槽执行占位（实际执行由外部注入）
    async def placeholder(input_data, context):
        return {"status": "registered", "slot": req.name, "input": input_data}
    slot = Slot(req.name, req.description, placeholder, req.category)
    reg.register(slot)
    return {"success": True, "slot": {"name": req.name, "description": req.description, "category": req.category}}


# ─── v3 新端点：工具注册表 ───

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


# ─── v3 新端点：Agent 状态 ───

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
    if req.task_queue is not None:
        data["task_queue"] = req.task_queue
    if req.history is not None:
        data["history"] = req.history
    if req.context is not None:
        data["context"] = req.context
    if req.reputation is not None:
        data["reputation"] = req.reputation
    if req.balance is not None:
        data["balance"] = req.balance
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


# ─── v3 新端点：Agent 间交易 ───

class TradeRequest(PydanticBaseModel):
    capability: str = Field(..., description="所需能力")
    task_params: dict = Field(default_factory=dict, description="任务参数")
    site_id: str = Field(default="auto-trade", description="交易ID")


@router.post("/trade", summary="Agent 间交易闭环")
async def agent_trade_endpoint(req: TradeRequest):
    """
    发现外部Agent → 协商 → 托管 → 执行 → 验证 → 结算
    """
    result = await execute_agent_trade(
        capability=req.capability,
        task_params=req.task_params,
        site_id=req.site_id,
    )
    return result
