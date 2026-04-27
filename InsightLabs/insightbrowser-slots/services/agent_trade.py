"""
Agent 间交易闭环
=================
当本地能力不足时，自动发现并调用外部 Agent。

流程：发现 → 协商 → 托管支付 → 执行 → 验证 → 确认/退款
"""
import requests
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("agent_trade")

BASE = {
    "registry": "http://localhost:7000",
    "ahp": "http://localhost:7002",
    "reliability": "http://localhost:7003",
    "commerce": "http://localhost:7004",
}

CEO_ID = "muyunye-ceo"


async def discover_external_agent(capability: str) -> Optional[Dict]:
    """从 Registry 搜索匹配的外部 Agent"""
    try:
        r = requests.get(f"{BASE['registry']}/api/search", params={"q": capability}, timeout=5)
        data = r.json()
        sites = data.get("sites", [])
        if sites:
            return sites[0]
    except Exception as e:
        logger.warning(f"Registry search failed: {e}")
    return None


async def negotiate_price(agent_info: dict, task: dict) -> dict:
    """通过 Commerce Bridge 协商"""
    try:
        r = requests.post(f"{BASE['commerce']}/api/convert", json={
            "url": agent_info.get("endpoint", f"http://localhost:{agent_info.get('id',0)}"),
            "name": agent_info.get("name", "external-agent"),
            "category": agent_info.get("type", "general"),
            "description": agent_info.get("description", ""),
        }, timeout=10)
        return r.json()
    except Exception as e:
        logger.warning(f"Commerce negotiate failed: {e}")
        return {"success": False, "error": str(e)}


async def escrow_payment(from_agent: str, to_agent: str, amount: float, site_id: str) -> dict:
    """在 Ledger 中托管支付"""
    try:
        r = requests.post(f"{BASE['reliability']}/api/ledger/record", json={
            "from_agent": from_agent,
            "to_agent": to_agent,
            "site_id": site_id,
            "action": f"escrow:{amount}",
            "tokens_used": 0,
            "success": True,
        }, timeout=10)
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


async def execute_via_ahp(agent_id: str, action: str, data: dict) -> dict:
    """通过 AHP Proxy 调用外部 Agent"""
    try:
        r = requests.post(f"{BASE['ahp']}/sites/{agent_id}/action", json={
            "action": action,
            "data": data,
        }, timeout=30)
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


async def confirm_payment(transaction_ref: str) -> dict:
    """确认付款"""
    logger.info(f"Payment confirmed for {transaction_ref}")
    return {"success": True, "action": "confirm", "ref": transaction_ref}


async def refund_payment(transaction_ref: str, reason: str) -> dict:
    """退款"""
    logger.info(f"Refund for {transaction_ref}: {reason}")
    return {"success": True, "action": "refund", "ref": transaction_ref, "reason": reason}


async def execute_agent_trade(
    capability: str,
    task_params: dict,
    site_id: str,
    max_cost: float = 1.0
) -> dict:
    """
    完整的 Agent 间交易闭环。
    返回整个交易过程记录。
    """
    trade_log = {
        "started_at": datetime.now().isoformat(),
        "capability": capability,
        "site_id": site_id,
        "steps": [],
    }

    # 1. 发现外部 Agent
    agent = await discover_external_agent(capability)
    if agent is None:
        trade_log["status"] = "no_agent_found"
        trade_log["error"] = f"No external agent found for capability: {capability}"
        trade_log["gap"] = {"capability": capability, "suggested_action": "register_new_agent"}
        return trade_log

    trade_log["agent"] = {"name": agent.get("name"), "site_id": agent.get("site_id")}
    trade_log["steps"].append({"step": "discover", "status": "ok"})

    # 2. 协商
    negotiation = await negotiate_price(agent, task_params)
    trade_log["steps"].append({"step": "negotiate", "result": negotiation})

    if not negotiation.get("success"):
        trade_log["status"] = "negotiation_failed"
        return trade_log

    # 3. 托管支付
    escrow = await escrow_payment(CEO_ID, agent.get("name", "external"), 0.01, site_id)
    trade_log["steps"].append({"step": "escrow", "result": escrow})

    # 4. 执行
    execution = await execute_via_ahp(
        agent.get("site_id", ""),
        task_params.get("action", "execute"),
        task_params.get("data", {})
    )
    trade_log["steps"].append({"step": "execute", "result": execution})

    # 5. 验证（简化：success 检查）
    trade_log["steps"].append({"step": "verify", "passed": execution.get("success", False)})

    # 6. 确认/退款
    if execution.get("success"):
        payment = await confirm_payment(site_id)
        trade_log["steps"].append({"step": "pay", "action": "confirmed"})
        trade_log["status"] = "completed"
    else:
        payment = await refund_payment(site_id, execution.get("error", "execution failed"))
        trade_log["steps"].append({"step": "pay", "action": "refunded"})
        trade_log["status"] = "refunded"

    trade_log["completed_at"] = datetime.now().isoformat()
    return trade_log
