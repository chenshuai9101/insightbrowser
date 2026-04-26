"""InsightBrowser Reliability — Heartbeat Health Check Engine

Runs as an async background task, periodically pinging all registered
sites and recording their status in the reliability database.

Pings check:
1. Registry (port 7000) — GET /health
2. AHP Proxy (port 7002) — GET /health  
3. Each tracked AHP site — GET /info endpoint
"""
import asyncio
import logging
import time
from typing import Optional

import httpx

from models import get_conn

logger = logging.getLogger("reliability.heartbeater")

# ─── Configuration ──────────────────────────────────────────────────

HEARTBEAT_INTERVAL = 30  # seconds between full check cycles
HTTP_TIMEOUT = 10         # seconds per ping

# Known internal services (auto-tracked for health)
KNOWN_SERVICES = {
    "registry": {"name": "InsightBrowser Registry", "url": "http://localhost:7000/health"},
    "ahp_proxy": {"name": "AHP Proxy", "url": "http://localhost:7002/health"},
    "hosting": {"name": "InsightBrowser Hosting", "url": "http://localhost:7001/health"},
}


# ─── Heartbeat Engine ───────────────────────────────────────────────

class Heartbeater:
    """Async heartbeat checker for all tracked sites."""

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._client: Optional[httpx.AsyncClient] = None

    async def start(self):
        """Start the heartbeat loop in the background."""
        if self._running:
            return
        self._running = True
        self._client = httpx.AsyncClient(timeout=HTTP_TIMEOUT)
        # Auto-register known services before starting the loop
        self._ensure_known_services()
        self._task = asyncio.create_task(self._loop())
        logger.info("Heartbeater started (interval=%ds)", HEARTBEAT_INTERVAL)

    def _ensure_known_services(self):
        """Register known services in the sites table if not already present."""
        from models import get_conn
        conn = get_conn()
        for site_id, info in KNOWN_SERVICES.items():
            existing = conn.execute(
                "SELECT site_id FROM sites WHERE site_id = ?", (site_id,)
            ).fetchone()
            if not existing:
                conn.execute(
                    """INSERT INTO sites (site_id, name, site_type, description, endpoint)
                       VALUES (?, ?, ?, ?, ?)""",
                    (site_id, info["name"], "system", f"Internal service: {info['name']}", info["url"]),
                )
        conn.commit()

    async def stop(self):
        """Stop the heartbeat loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("Heartbeater stopped")

    async def ping_site(self, site_id: str, name: str, url: str) -> dict:
        """Ping a single site and record the result."""
        start = time.monotonic()
        status = "alive"
        response_time_ms = 0
        error = None

        try:
            assert self._client is not None
            resp = await self._client.get(url, follow_redirects=True)
            response_time_ms = int((time.monotonic() - start) * 1000)
            if resp.status_code >= 500:
                status = "error"
                error = f"HTTP {resp.status_code}"
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            status = "dead"
            response_time_ms = int((time.monotonic() - start) * 1000)
            error = str(e.__class__.__name__)
        except Exception as e:
            status = "error"
            response_time_ms = int((time.monotonic() - start) * 1000)
            error = str(e)

        # Record heartbeat
        conn = get_conn()
        conn.execute(
            """INSERT INTO heartbeats (site_id, status, response_time_ms)
               VALUES (?, ?, ?)""",
            (site_id, status, response_time_ms),
        )

        # Update site's last_seen if alive
        if status == "alive":
            conn.execute(
                "UPDATE sites SET last_seen = datetime('now') WHERE site_id = ?",
                (site_id,),
            )

        conn.commit()

        logger.debug(
            "Heartbeat %s → %s (%s, %dms)",
            site_id, status, name, response_time_ms,
        )

        return {
            "site_id": site_id,
            "name": name,
            "status": status,
            "response_time_ms": response_time_ms,
            "error": error,
        }

    async def ping_all(self) -> list[dict]:
        """Ping all tracked sites (known services + registered AHP sites)."""
        results = []

        # 1. Ping known internal services
        for site_id, info in KNOWN_SERVICES.items():
            try:
                result = await self.ping_site(
                    site_id, info["name"], info["url"]
                )
                results.append(result)
            except Exception as e:
                logger.warning("Failed to ping %s: %s", site_id, e)

        # 2. Ping all tracked AHP sites
        conn = get_conn()
        rows = conn.execute(
            "SELECT site_id, name, endpoint FROM sites WHERE endpoint != ''"
        ).fetchall()

        for row in rows:
            site_id = row["site_id"]
            name = row["name"]
            endpoint = row["endpoint"]

            # Build ping URL — try /info endpoint
            ping_url = endpoint.rstrip("/") + "/info"
            try:
                result = await self.ping_site(site_id, name, ping_url)
                results.append(result)
            except Exception as e:
                logger.warning("Failed to ping site %s: %s", site_id, e)

        return results

    async def ping_site_by_id(self, site_id: str) -> dict:
        """Ping a specific site by its ID (used for manual triggers)."""
        # Check KNOWN_SERVICES first
        if site_id in KNOWN_SERVICES:
            info = KNOWN_SERVICES[site_id]
            return await self.ping_site(site_id, info["name"], info["url"])

        # Check database
        conn = get_conn()
        row = conn.execute(
            "SELECT site_id, name, endpoint FROM sites WHERE site_id = ?",
            (site_id,),
        ).fetchone()

        if not row:
            return {
                "site_id": site_id,
                "status": "unknown",
                "error": "Site not found in tracking database",
            }

        endpoint = row["endpoint"]
        if not endpoint:
            return {
                "site_id": site_id,
                "status": "unknown",
                "error": "Site has no endpoint configured",
            }

        ping_url = endpoint.rstrip("/") + "/info"
        return await self.ping_site(
            row["site_id"], row["name"], ping_url
        )

    async def _loop(self):
        """Main heartbeat loop — runs every HEARTBEAT_INTERVAL seconds."""
        while self._running:
            try:
                results = await self.ping_all()
                alive = sum(1 for r in results if r.get("status") == "alive")
                dead = sum(1 for r in results if r.get("status") == "dead")
                logger.info(
                    "Heartbeat cycle complete: %d alive, %d dead, %d total",
                    alive, dead, len(results),
                )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Heartbeat cycle error: %s", e)

            await asyncio.sleep(HEARTBEAT_INTERVAL)


# ─── Global instance ─────────────────────────────────────────────────

heartbeater = Heartbeater()
