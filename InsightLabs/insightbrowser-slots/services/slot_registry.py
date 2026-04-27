"""
开放式卡槽注册表
=================
任何开发者可注册自定义卡槽类型。
不再局限于内置五卡槽。
"""
import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("slot_registry")

# 卡槽接口
class Slot:
    """一个可注册的卡槽"""
    def __init__(self, name: str, description: str, execute: Callable, category: str = "core"):
        self.name = name
        self.description = description
        self.execute = execute   # async def execute(input: dict, context: dict) -> dict
        self.category = category  # core | extension | custom


class SlotRegistry:
    """开放式卡槽注册中心"""

    def __init__(self):
        self._slots: Dict[str, Slot] = {}

        # 注册五大核心卡槽（占位，实际由 engine 提供实现）
        self._slots["perception"] = Slot("perception", "感知卡槽：理解需求", None, "core")
        self._slots["planning"] = Slot("planning", "规划卡槽：拆分任务", None, "core")
        self._slots["execution"] = Slot("execution", "执行卡槽：调用能力", None, "core")
        self._slots["synthesis"] = Slot("synthesis", "合成卡槽：汇总结果", None, "core")
        self._slots["verification"] = Slot("verification", "验证卡槽：质量检查", None, "core")

    def register(self, slot: Slot) -> "SlotRegistry":
        self._slots[slot.name] = slot
        logger.info(f"Slot registered: {slot.name} ({slot.category})")
        return self

    def unregister(self, name: str) -> bool:
        if name in self._slots and name not in ("perception", "planning", "execution", "synthesis", "verification"):
            del self._slots[name]
            return True
        return False

    def get(self, name: str) -> Optional[Slot]:
        return self._slots.get(name)

    def list_all(self) -> List[dict]:
        return [
            {"name": s.name, "description": s.description, "category": s.category}
            for s in self._slots.values()
        ]

    def list_by_category(self, category: str) -> List[dict]:
        return [
            {"name": s.name, "description": s.description}
            for s in self._slots.values() if s.category == category
        ]

    def has(self, name: str) -> bool:
        return name in self._slots


# 全局单例
_slot_registry = SlotRegistry()

def get_slot_registry() -> SlotRegistry:
    return _slot_registry
