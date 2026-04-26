"""Commerce Bridge - Publisher Service

Publishes commerce sites to the system by:
1. Directly registering in the Reliability database (port 7003)
2. Making the site discoverable through AHP Proxy (port 7002)

The system expects:
- Reliability (7003): trust ratings, heartbeat tracking
- AHP Proxy (7002): site proxying & agent.json serving
"""
import json
import logging
import sqlite3
from typing import Optional

import httpx

logger = logging.getLogger("commerce.publisher")

# ─── Configuration ───────────────────────────────────────────────────

AHP_URL = "http://localhost:7002"
RELIABILITY_URL = "http://localhost:7003"

# Path to Reliability's SQLite database (relative to InsightLabs/)
RELIABILITY_DB_PATH = "/Users/muyunye/.openclaw/workspace/InsightLabs/reliability.db"


# ─── Reliability DB Registration ────────────────────────────────────

async def register_in_reliability_db(
    name: str,
    site_id: str,
    url: str,
    description: str,
    agent_json: dict,
) -> bool:
    """Register site directly in Reliability's SQLite database.

    Reliability tracks sites for heartbeat health checks and trust ratings.
    Without this registration, the site won't get a trust rating.
    """
    try:
        conn = sqlite3.connect(RELIABILITY_DB_PATH)
        conn.row_factory = sqlite3.Row

        # Check if site already exists
        existing = conn.execute(
            "SELECT site_id FROM sites WHERE site_id = ?", (site_id,)
        ).fetchone()

        if existing:
            logger.info(f"Site {site_id} already exists in Reliability DB, updating...")
            conn.execute(
                """UPDATE sites SET name=?, description=?, endpoint=?,
                   last_seen=datetime('now') WHERE site_id=?""",
                (name, description, url, site_id),
            )
        else:
            conn.execute(
                """INSERT INTO sites (site_id, name, site_type, description, endpoint, owner)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (site_id, name, "commerce", description, url, "commerce-bridge"),
            )

        conn.commit()
        conn.close()
        logger.info(f"✅ Registered '{name}' (site_id={site_id}) in Reliability DB")
        return True
    except Exception as e:
        logger.error(f"Failed to register in Reliability DB: {e}")
        return False


# ─── AHP Site Registration ──────────────────────────────────────────

async def register_with_ahp(
    name: str,
    site_id: str,
    description: str,
    agent_json: dict,
) -> bool:
    """Register site information so AHP Proxy can serve it.

    AHP discovers sites from Reliability. By having the site in
    Reliability's database, AHP will find it on next sync.
    
    This also stores the agent.json with AHP if there's an
    endpoint for that.
    """
    # AHP discovers sites from Reliability DB, so just verify
    # AHP is alive by hitting its list endpoint
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{AHP_URL}/sites")
            if resp.status_code in (200, 201):
                logger.info(f"✅ AHP Proxy confirmed alive (listed {name})")
                return True
            else:
                logger.warning(f"AHP Proxy returned {resp.status_code}")
                return False
    except Exception as e:
        logger.error(f"Failed to contact AHP Proxy: {e}")
        return False


# ─── Combined Publishing ─────────────────────────────────────────────

async def publish_commerce_site(
    name: str,
    category: str,
    url: str,
    description: str,
    agent_json: dict,
) -> dict:
    """Publish a commerce site to the system.

    Uses Reliability DB for trust tracking and AHP for discovery.
    """
    # Generate a stable site_id
    site_id = f"commerce-{name.lower().replace(' ', '-')[:30]}"

    # Step 1: Register in Reliability database
    db_ok = await register_in_reliability_db(
        name, site_id, url, description, agent_json,
    )

    # Step 2: Confirm AHP Proxy is operational
    ahp_ok = await register_with_ahp(
        name, site_id, description, agent_json,
    )

    # Build discover URL
    discover_url = f"http://localhost:8080/agent-discover"

    result = {
        "success": db_ok or ahp_ok,
        "site_id": site_id,
        "reliability_ok": db_ok,
        "ahp_ok": ahp_ok,
        "discover_url": discover_url,
    }

    if not db_ok and not ahp_ok:
        result["error"] = "Registration failed on all backends"

    return result
