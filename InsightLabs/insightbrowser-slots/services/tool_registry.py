"""
工具注册表 — 每个 capability 关联真实工具
=========================================
Tools > Prompts。执行卡槽优先用工具执行，无匹配工具才 fallback LLM。

Tool 接口:
- name: 工具名
- description: 描述
- input_schema: dict, 输入参数定义
- execute(params) -> dict: 同步或异步执行
"""
import json
import logging
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("tool_registry")


class Tool:
    """单个工具定义"""
    def __init__(self, name: str, description: str, input_schema: dict, execute: Callable):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.execute = execute   # async def execute(params: dict) -> dict

    def to_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


class ToolRegistry:
    """工具注册中心"""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}           # name → Tool
        self._capability_tools: Dict[str, List[str]] = {}  # capability → [tool_names]

    def register(self, tool: Tool) -> "ToolRegistry":
        self._tools[tool.name] = tool
        return self

    def bind_to_capability(self, capability: str, tool_names: List[str]) -> "ToolRegistry":
        self._capability_tools[capability] = tool_names
        return self

    def get_tools_for_capability(self, capability: str) -> List[Tool]:
        """获取某个能力类型对应的工具列表"""
        names = self._capability_tools.get(capability, [])
        return [self._tools[n] for n in names if n in self._tools]

    def get_tool(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_all(self) -> List[dict]:
        return [t.to_schema() for t in self._tools.values()]

    def list_capabilities(self) -> List[str]:
        return list(self._capability_tools.keys())

    async def execute_with_tools(self, capability: str, params: dict,
                                  context: dict = None) -> dict:
        """用工具执行某个能力，按优先级顺序尝试"""
        tools = self.get_tools_for_capability(capability)
        if not tools:
            return {"success": False, "error": f"No tools for capability '{capability}'",
                    "fallback_to_llm": True}

        results = []
        for tool in tools:
            try:
                result = await tool.execute({**params, **({} if context is None else context)})
                results.append({"tool": tool.name, "result": result, "success": True})
            except Exception as e:
                results.append({"tool": tool.name, "error": str(e), "success": False})

        return {
            "success": True,
            "capability": capability,
            "tools_used": len(tools),
            "results": results,
        }

    def has_tools_for(self, capability: str) -> bool:
        return capability in self._capability_tools and len(self._capability_tools[capability]) > 0


# ─── 全局单例 ───

_tool_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    return _tool_registry
