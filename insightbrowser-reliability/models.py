"""InsightBrowser Reliability — Data Models & SQLite Schema

Stores trust metrics, heartbeat records, and credit transactions
for the Agent Reliability & Credit Ledger system.
"""
import json
import sqlite3
import threading
import time
from typing import Optional

# ─── Database path ─────────────────────────────────────────────────────

DB_PATH = "reliability.db"

# ─── Thread-local connection ───────────────────────────────────────────

_local = threading.local()


def get_conn() -> sqlite3.Connection:
    """Get a thread-local SQLite connection."""
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(DB_PATH)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sites (
            site_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            site_type TEXT DEFAULT 'general',
            description TEXT DEFAULT '',
            endpoint TEXT DEFAULT '',
            owner TEXT DEFAULT '',
            registered_at TEXT DEFAULT (datetime('now')),
            last_seen TEXT,
            total_calls INTEGER DEFAULT 0,
            successful_calls INTEGER DEFAULT 0,
            failed_calls INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS heartbeats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'unknown',
            response_time_ms INTEGER DEFAULT 0,
            checked_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (site_id) REFERENCES sites(site_id)
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_agent TEXT NOT NULL,
            to_agent TEXT NOT NULL,
            site_id TEXT NOT NULL,
            action TEXT NOT NULL DEFAULT '',
            tokens_used INTEGER DEFAULT 0,
            credit_cost INTEGER DEFAULT 1,
            success INTEGER NOT NULL DEFAULT 1,
            timestamp TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS agent_accounts (
            agent_id TEXT PRIMARY KEY,
            balance INTEGER DEFAULT 1000,
            total_calls INTEGER DEFAULT 0,
            total_spent INTEGER DEFAULT 0,
            total_earned INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_heartbeats_site ON heartbeats(site_id, checked_at);
        CREATE INDEX IF NOT EXISTS idx_transactions_site ON transactions(site_id);
        CREATE INDEX IF NOT EXISTS idx_transactions_from ON transactions(from_agent);
        CREATE INDEX IF NOT EXISTS idx_transactions_to ON transactions(to_agent);
        CREATE INDEX IF NOT EXISTS idx_transactions_time ON transactions(timestamp);
    """)
    conn.commit()


# ─── Site ──────────────────────────────────────────────────────────────

class SiteRecord:
    """A tracked site in the Reliability Registry."""

    def __init__(self, row: sqlite3.Row):
        self.site_id: str = row["site_id"]
        self.name: str = row["name"]
        self.site_type: str = row["site_type"]
        self.description: str = row["description"]
        self.endpoint: str = row["endpoint"]
        self.owner: str = row["owner"]
        self.registered_at: str = row["registered_at"]
        self.last_seen: Optional[str] = row["last_seen"]
        self.total_calls: int = row["total_calls"]
        self.successful_calls: int = row["successful_calls"]
        self.failed_calls: int = row["failed_calls"]

    def to_dict(self) -> dict:
        return {
            "site_id": self.site_id,
            "name": self.name,
            "site_type": self.site_type,
            "description": self.description,
            "endpoint": self.endpoint,
            "owner": self.owner,
            "registered_at": self.registered_at,
            "last_seen": self.last_seen,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
        }


# ─── Transaction ──────────────────────────────────────────────────────

class Transaction:
    """Record of an agent-to-agent call."""

    def __init__(self, row: sqlite3.Row):
        self.id: int = row["id"]
        self.from_agent: str = row["from_agent"]
        self.to_agent: str = row["to_agent"]
        self.site_id: str = row["site_id"]
        self.action: str = row["action"]
        self.tokens_used: int = row["tokens_used"]
        self.credit_cost: int = row["credit_cost"]
        self.success: bool = bool(row["success"])
        self.timestamp: str = row["timestamp"]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "site_id": self.site_id,
            "action": self.action,
            "tokens_used": self.tokens_used,
            "credit_cost": self.credit_cost,
            "success": self.success,
            "timestamp": self.timestamp,
        }


# ─── Agent Account ────────────────────────────────────────────────────

class AgentAccount:
    """Credit account for an agent."""

    def __init__(self, row: sqlite3.Row):
        self.agent_id: str = row["agent_id"]
        self.balance: int = row["balance"]
        self.total_calls: int = row["total_calls"]
        self.total_spent: int = row["total_spent"]
        self.total_earned: int = row["total_earned"]
        self.created_at: str = row["created_at"]

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "balance": self.balance,
            "total_calls": self.total_calls,
            "total_spent": self.total_spent,
            "total_earned": self.total_earned,
            "created_at": self.created_at,
        }
