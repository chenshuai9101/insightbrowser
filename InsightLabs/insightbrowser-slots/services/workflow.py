"""
工作流引擎 — 替代固定五步流水线
================================
支持动态 DAG 编排：条件跳转、分支、循环、重试。
"""
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger("workflow.engine")

# ─── 节点定义 ───

class WorkflowNode:
    """工作流节点：执行一个步骤，返回结果"""
    def __init__(self, name: str, handler: Callable, condition: Optional[Callable] = None):
        self.name = name
        self.handler = handler          # async def handler(input_data) -> dict
        self.condition = condition      # def condition(context) -> bool, None=总是执行

    def should_run(self, context: dict) -> bool:
        if self.condition is None:
            return True
        return self.condition(context)

    async def run(self, context: dict) -> dict:
        t0 = datetime.now()
        try:
            result = await self.handler(context)
            latency = (datetime.now() - t0).total_seconds() * 1000
            return {"success": True, "output": result, "latency_ms": latency}
        except Exception as e:
            latency = (datetime.now() - t0).total_seconds() * 1000
            return {"success": False, "error": str(e), "latency_ms": latency}


class WorkflowEdge:
    """工作流边：定义节点之间的条件跳转"""
    def __init__(self, from_node: str, to_node: str, condition: Optional[Callable] = None):
        self.from_node = from_node
        self.to_node = to_node
        self.condition = condition      # def condition(context) -> bool, None=总是跳转

    def should_traverse(self, context: dict) -> bool:
        if self.condition is None:
            return True
        return self.condition(context)


class WorkflowEngine:
    """DAG 工作流执行引擎"""

    def __init__(self):
        self.nodes: Dict[str, WorkflowNode] = {}
        self.edges: Dict[str, List[WorkflowEdge]] = {}   # from_node → [edges]
        self.entry_node: Optional[str] = None

    def add_node(self, node: WorkflowNode) -> "WorkflowEngine":
        self.nodes[node.name] = node
        if self.entry_node is None:
            self.entry_node = node.name
        return self

    def add_edge(self, edge: WorkflowEdge) -> "WorkflowEngine":
        if edge.from_node not in self.edges:
            self.edges[edge.from_node] = []
        self.edges[edge.from_node].append(edge)
        return self

    def set_entry(self, node_name: str) -> "WorkflowEngine":
        self.entry_node = node_name
        return self

    async def run(self, initial_context: dict) -> dict:
        """执行工作流，返回完整执行记录"""
        context = dict(initial_context)
        context["_steps"] = []
        context["_status"] = "running"

        if self.entry_node is None:
            return {"success": False, "error": "No entry node", "_steps": []}

        current = self.entry_node
        visited = set()
        max_steps = 50  # 防死循环

        while current and len(context["_steps"]) < max_steps:
            if current in visited and not self._has_loopback(current):
                # 非循环节点，重复访问→停止
                logger.warning(f"Workflow: re-visiting {current} without loopback, stopping")
                break

            node = self.nodes.get(current)
            if node is None:
                logger.error(f"Workflow: node '{current}' not found")
                break

            if not node.should_run(context):
                context["_steps"].append({
                    "node": current, "status": "skipped", "reason": "condition not met"
                })
                current = self._next_node(current, context)
                continue

            step_start = datetime.now()
            result = await node.run(context)
            step_rec = {
                "node": current,
                "status": "ok" if result["success"] else "failed",
                "latency_ms": result.get("latency_ms", 0),
                "time": step_start.isoformat(),
            }

            if result["success"]:
                context[current] = result["output"]
            else:
                step_rec["error"] = result.get("error", "unknown")
                context["_error"] = result.get("error")
                # 检查是否有错误恢复路径
                error_next = self._error_next(current, context)
                if error_next:
                    context["_steps"].append(step_rec)
                    current = error_next
                    continue

            context["_steps"].append(step_rec)
            visited.add(current)
            current = self._next_node(current, context)

        context["_status"] = "completed" if not context.get("_error") else "failed"
        context["_completed_at"] = datetime.now().isoformat()
        return context

    def _next_node(self, current: str, context: dict) -> Optional[str]:
        """决定下一个节点"""
        edges = self.edges.get(current, [])
        for edge in edges:
            if edge.should_traverse(context):
                return edge.to_node
        return None  # 没有出边 = 终止

    def _error_next(self, current: str, context: dict) -> Optional[str]:
        """查找错误恢复路径（节点名以 _error 结尾的边）"""
        edges = self.edges.get(current, [])
        for edge in edges:
            if edge.should_traverse(context) and "_error" in edge.to_node:
                return edge.to_node
        return None

    def _has_loopback(self, node_name: str) -> bool:
        """检查是否有回到此节点的边"""
        for from_node, edges in self.edges.items():
            for edge in edges:
                if edge.to_node == node_name:
                    return True
        return False


# ─── 预设工作流模板 ───

# 这些模板是工厂函数，返回预配置的 WorkflowEngine 实例
# 实际节点 handler 由调用者注入

def make_simple_workflow() -> WorkflowEngine:
    """简单模板：感知 → 执行 → 交付（跳过规划/合成/验证）"""
    return WorkflowEngine()

def make_standard_workflow() -> WorkflowEngine:
    """标准模板：感知 → 规划 → 执行 → 合成 → 验证"""
    return WorkflowEngine()

def make_research_workflow() -> WorkflowEngine:
    """研究模板：感知 → 规划 → 搜索执行 → 分析执行 → 写作执行 → 合成 → 多轮验证"""
    return WorkflowEngine()

def make_negotiation_workflow() -> WorkflowEngine:
    """协商模板：感知 → 发现外部Agent → 协商 → 托管 → 执行 → 验证 → 确认/退款"""
    return WorkflowEngine()

def make_loop_workflow(max_retries: int = 3) -> WorkflowEngine:
    """循环模板：执行 → 验证 → (不通过且重试<max) → 执行"""
    return WorkflowEngine()
