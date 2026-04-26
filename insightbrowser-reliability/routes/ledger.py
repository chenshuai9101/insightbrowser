"""InsightBrowser Reliability — Credit Ledger API Routes

Endpoints:
- POST /api/ledger/record              → Record an agent-to-agent call
- GET  /api/ledger/agent/{agent_id}    → Agent's transaction history
- GET  /api/ledger/transactions        → All transactions (paginated)
- GET  /api/ledger/agent/{agent_id}/balance → Agent's current balance
- POST /api/ledger/agent/{agent_id}/create → Create a new account
- GET  /api/ledger/leaderboard         → Credit leaderboard
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from services.ledger import ledger_service

logger = logging.getLogger("reliability.routes.ledger")
router = APIRouter(prefix="/api/ledger", tags=["Credit Ledger"])


# ─── Record Transaction ────────────────────────────────────────────────

@router.post("/record")
async def record_transaction(body: dict):
    """Record an agent-to-agent call as a transaction.

    Request body:
    ```json
    {
        "from_agent": "agent_A",
        "to_agent": "agent_B",
        "site_id": "site_123",
        "action": "analyze",
        "tokens_used": 500,
        "success": true
    }
    ```
    """
    from_agent = body.get("from_agent", "")
    to_agent = body.get("to_agent", "")
    site_id = body.get("site_id", "")
    action = body.get("action", "")
    tokens_used = int(body.get("tokens_used", 0))
    success = bool(body.get("success", True))

    if not from_agent or not to_agent or not site_id:
        raise HTTPException(
            status_code=400,
            detail="from_agent, to_agent, and site_id are required",
        )

    result = ledger_service.record_transaction(
        from_agent=from_agent,
        to_agent=to_agent,
        site_id=site_id,
        action=action,
        tokens_used=tokens_used,
        success=success,
    )

    if not result.get("success"):
        raise HTTPException(status_code=402, detail=result.get("error", "Transaction failed"))

    return {
        "success": True,
        "transaction": result,
    }


# ─── Agent Transaction History ────────────────────────────────────────

@router.get("/agent/{agent_id}")
async def get_agent_transactions(
    agent_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Get transaction history for a specific agent."""
    transactions = ledger_service.get_transactions(
        agent_id=agent_id, limit=limit, offset=offset
    )
    return {
        "success": True,
        "agent_id": agent_id,
        "total": len(transactions),
        "transactions": transactions,
    }


# ─── All Transactions ──────────────────────────────────────────────────

@router.get("/transactions")
async def get_all_transactions(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Get all transactions (paginated)."""
    transactions = ledger_service.get_transactions(limit=limit, offset=offset)
    return {
        "success": True,
        "total": len(transactions),
        "transactions": transactions,
    }


# ─── Agent Balance ─────────────────────────────────────────────────────

@router.get("/agent/{agent_id}/balance")
async def get_agent_balance(agent_id: str):
    """Get an agent's current credit balance."""
    account = ledger_service.get_balance(agent_id)
    if not account:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    return {
        "success": True,
        "agent_id": agent_id,
        "balance": account["balance"],
        "total_calls": account["total_calls"],
        "total_spent": account["total_spent"],
        "total_earned": account["total_earned"],
        "account": account,
    }


# ─── Create Account ────────────────────────────────────────────────────

@router.post("/agent/{agent_id}/create")
async def create_agent_account(agent_id: str):
    """Create a new agent account with initial credits."""
    try:
        account = ledger_service.create_account(agent_id)
        return {
            "success": True,
            "agent_id": account.agent_id,
            "balance": account.balance,
            "message": f"Account created with {account.balance} initial credits",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Leaderboard ───────────────────────────────────────────────────────

@router.get("/leaderboard")
async def get_credit_leaderboard(
    limit: int = Query(20, ge=1, le=100),
):
    """Get credit leaderboard sorted by balance."""
    leaderboard = ledger_service.get_leaderboard(limit=limit)
    return {
        "success": True,
        "total": len(leaderboard),
        "leaderboard": leaderboard,
    }
