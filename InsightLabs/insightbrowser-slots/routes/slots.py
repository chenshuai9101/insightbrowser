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
        "service": "InsightBrowser Slots",
        "total_calls": total_calls,
        "total_errors": total_errors,
        "error_rate": f"{total_errors / max(total_calls, 1) * 100:.2f}%",
        "slots": metrics,
    }
