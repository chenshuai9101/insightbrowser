"""InsightBrowser Reliability — Credit Ledger Service

Manages agent accounts, transaction recording, and credit balances.

Economic model:
- New agents get 1000 initial credits
- Each call costs: base(1) + (tokens_used / 1000)
- Called party earns: cost × 0.8 (20% platform fee)
"""
import logging
from typing import Optional

from models import get_conn, Transaction, AgentAccount

logger = logging.getLogger("reliability.ledger")


# ─── Constants ──────────────────────────────────────────────────────

INITIAL_CREDITS = 1000
BASE_COST = 1
PLATFORM_FEE_RATE = 0.20  # 20%


# ─── Ledger Service ─────────────────────────────────────────────────

class LedgerService:
    """Credit ledger service — manages agent accounts & transactions."""

    def create_account(self, agent_id: str) -> AgentAccount:
        """Create a new agent account with initial credits."""
        conn = get_conn()
        existing = conn.execute(
            "SELECT * FROM agent_accounts WHERE agent_id = ?",
            (agent_id,),
        ).fetchone()

        if existing:
            logger.info("Account already exists for %s", agent_id)
            return AgentAccount(existing)

        conn.execute(
            """INSERT INTO agent_accounts (agent_id, balance)
               VALUES (?, ?)""",
            (agent_id, INITIAL_CREDITS),
        )
        conn.commit()

        row = conn.execute(
            "SELECT * FROM agent_accounts WHERE agent_id = ?",
            (agent_id,),
        ).fetchone()
        logger.info("Created account for %s with %d credits", agent_id, INITIAL_CREDITS)
        return AgentAccount(row)

    def get_balance(self, agent_id: str) -> Optional[dict]:
        """Get agent's current balance and account summary."""
        conn = get_conn()
        row = conn.execute(
            "SELECT * FROM agent_accounts WHERE agent_id = ?",
            (agent_id,),
        ).fetchone()

        if not row:
            return None
        return AgentAccount(row).to_dict()

    def record_transaction(
        self,
        from_agent: str,
        to_agent: str,
        site_id: str,
        action: str = "",
        tokens_used: int = 0,
        success: bool = True,
    ) -> dict:
        """Record an agent-to-agent call and update credit balances.

        Economic model:
        - cost = base(1) + (tokens_used / 1000)
        - caller's balance decreases by cost
        - called party's balance increases by cost × 0.8

        Returns transaction details.
        """
        # Ensure both accounts exist
        self.create_account(from_agent)
        self.create_account(to_agent)

        # Ensure site exists in tracking database
        self._ensure_site(site_id, to_agent)

        # Calculate credit cost
        credit_cost = BASE_COST + (tokens_used // 1000)

        conn = get_conn()

        # Check caller balance
        caller_row = conn.execute(
            "SELECT balance FROM agent_accounts WHERE agent_id = ?",
            (from_agent,),
        ).fetchone()

        caller_balance = caller_row["balance"] if caller_row else 0

        if caller_balance < credit_cost:
            logger.warning(
                "Insufficient credits for %s: have %d, need %d",
                from_agent, caller_balance, credit_cost,
            )
            return {
                "success": False,
                "error": "Insufficient credits",
                "credit_cost": credit_cost,
                "balance": caller_balance,
            }

        # Record transaction
        conn.execute(
            """INSERT INTO transactions
               (from_agent, to_agent, site_id, action, tokens_used, credit_cost, success)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (from_agent, to_agent, site_id, action, tokens_used, credit_cost,
             1 if success else 0),
        )

        # Update caller account
        earnings = int(credit_cost * (1 - PLATFORM_FEE_RATE))
        conn.execute(
            """UPDATE agent_accounts SET
               balance = balance - ?,
               total_calls = total_calls + 1,
               total_spent = total_spent + ?
               WHERE agent_id = ?""",
            (credit_cost, credit_cost, from_agent),
        )

        # Update called party account
        actual_earnings = max(earnings, 1) if credit_cost > 0 else 0
        conn.execute(
            """UPDATE agent_accounts SET
               balance = balance + ?,
               total_calls = total_calls + 1,
               total_earned = total_earned + ?
               WHERE agent_id = ?""",
            (actual_earnings, actual_earnings, to_agent),
        )

        # Update call stats on the site
        if success:
            conn.execute(
                """UPDATE sites SET total_calls = total_calls + 1,
                   successful_calls = successful_calls + 1
                   WHERE site_id = ?""",
                (site_id,),
            )
        else:
            conn.execute(
                """UPDATE sites SET total_calls = total_calls + 1,
                   failed_calls = failed_calls + 1
                   WHERE site_id = ?""",
                (site_id,),
            )

        conn.commit()

        logger.info(
            "Transaction: %s → %s (%s), cost=%d, earned=%d",
            from_agent, to_agent, site_id, credit_cost, earnings,
        )

        actual_earnings = max(earnings, 1) if credit_cost > 0 else 0
        return {
            "success": True,
            "from_agent": from_agent,
            "to_agent": to_agent,
            "site_id": site_id,
            "action": action,
            "tokens_used": tokens_used,
            "credit_cost": credit_cost,
            "earnings": actual_earnings,
            "platform_fee": credit_cost - actual_earnings,
            "new_caller_balance": caller_balance - credit_cost,
        }

    def get_transactions(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """Get transaction history, optionally filtered by agent."""
        conn = get_conn()

        if agent_id:
            rows = conn.execute(
                """SELECT * FROM transactions
                   WHERE from_agent = ? OR to_agent = ?
                   ORDER BY timestamp DESC LIMIT ? OFFSET ?""",
                (agent_id, agent_id, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM transactions ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()

        return [Transaction(r).to_dict() for r in rows]

    def _ensure_site(self, site_id: str, site_name: str):
        """Ensure a site exists in the tracking database."""
        conn = get_conn()
        existing = conn.execute(
            "SELECT site_id FROM sites WHERE site_id = ?", (site_id,)
        ).fetchone()
        if not existing:
            conn.execute(
                """INSERT INTO sites (site_id, name)
                   VALUES (?, ?)""",
                (site_id, site_name),
            )
            conn.commit()
            logger.info("Auto-registered site %s (%s)", site_id, site_name)

    def get_leaderboard(self, limit: int = 20) -> list[dict]:
        """Get credit leaderboard sorted by balance."""
        conn = get_conn()
        rows = conn.execute(
            """SELECT * FROM agent_accounts
               ORDER BY balance DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [AgentAccount(r).to_dict() for r in rows]


# ─── Global instance ─────────────────────────────────────────────────

ledger_service = LedgerService()
