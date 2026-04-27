"""
状态持久化 — Agent 状态存储
============================
基于 SQLite，支持跨会话恢复。
"""
import json
import sqlite3
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agent_state.db")


def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_state_db():
    conn = _get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_state (
            agent_id TEXT PRIMARY KEY,
            task_queue TEXT DEFAULT '[]',
            history TEXT DEFAULT '[]',
            context TEXT DEFAULT '{}',
            reputation REAL DEFAULT 0.5,
            balance REAL DEFAULT 0.0,
            last_active TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_state(agent_id: str) -> dict:
    conn = _get_db()
    row = conn.execute("SELECT * FROM agent_state WHERE agent_id = ?", (agent_id,)).fetchone()
    conn.close()
    if row is None:
        return {
            "agent_id": agent_id,
            "task_queue": [],
            "history": [],
            "context": {},
            "reputation": 0.5,
            "balance": 0.0,
            "last_active": None,
            "created_at": None,
            "updated_at": None,
            "found": False,
        }
    return {
        "agent_id": row["agent_id"],
        "task_queue": json.loads(row["task_queue"]),
        "history": json.loads(row["history"]),
        "context": json.loads(row["context"]),
        "reputation": row["reputation"],
        "balance": row["balance"],
        "last_active": row["last_active"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "found": True,
    }


def save_state(agent_id: str, data: dict):
    now = datetime.now().isoformat()
    conn = _get_db()

    existing = conn.execute("SELECT agent_id FROM agent_state WHERE agent_id = ?", (agent_id,)).fetchone()

    if existing:
        conn.execute("""
            UPDATE agent_state SET
                task_queue = ?,
                history = ?,
                context = ?,
                reputation = ?,
                balance = ?,
                last_active = ?,
                updated_at = ?
            WHERE agent_id = ?
        """, (
            json.dumps(data.get("task_queue", []), ensure_ascii=False),
            json.dumps(data.get("history", []), ensure_ascii=False),
            json.dumps(data.get("context", {}), ensure_ascii=False),
            data.get("reputation", 0.5),
            data.get("balance", 0.0),
            now,
            now,
            agent_id,
        ))
    else:
        conn.execute("""
            INSERT INTO agent_state (agent_id, task_queue, history, context, reputation, balance, last_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            agent_id,
            json.dumps(data.get("task_queue", []), ensure_ascii=False),
            json.dumps(data.get("history", []), ensure_ascii=False),
            json.dumps(data.get("context", {}), ensure_ascii=False),
            data.get("reputation", 0.5),
            data.get("balance", 0.0),
            now, now, now,
        ))
    conn.commit()
    conn.close()


def append_history(agent_id: str, entry: dict):
    """追加历史记录"""
    state = get_state(agent_id)
    history = state.get("history", [])
    entry["timestamp"] = datetime.now().isoformat()
    history.append(entry)
    # 保留最近 100 条
    if len(history) > 100:
        history = history[-100:]
    state["history"] = history
    save_state(agent_id, state)


def push_task(agent_id: str, task: dict):
    """添加到任务队列"""
    state = get_state(agent_id)
    queue = state.get("task_queue", [])
    task["queued_at"] = datetime.now().isoformat()
    queue.append(task)
    state["task_queue"] = queue
    save_state(agent_id, state)


def pop_task(agent_id: str) -> Optional[dict]:
    """弹出下一个任务"""
    state = get_state(agent_id)
    queue = state.get("task_queue", [])
    if not queue:
        return None
    task = queue.pop(0)
    state["task_queue"] = queue
    save_state(agent_id, state)
    return task


def list_agents() -> List[str]:
    conn = _get_db()
    rows = conn.execute("SELECT agent_id FROM agent_state ORDER BY updated_at DESC LIMIT 50").fetchall()
    conn.close()
    return [r["agent_id"] for r in rows]
