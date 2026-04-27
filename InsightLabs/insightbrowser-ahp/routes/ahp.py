"""InsightBrowser AHP - AHP Protocol Routes

Implements AHP v0.1 endpoints for each hosted site:
- GET  /sites/{site_id}        → agent.json
- GET  /sites/{site_id}/info   → AHP Info
- POST /sites/{site_id}/action → Execute capability
- POST /sites/{site_id}/data   → Get site data
- GET  /sites/{site_id}/stream → SSE stream

Also includes endpoints to discover available sites:
- GET  /sites                  → List all proxied sites
"""
import json
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from models import HostingSite, AHPInfo, AHPActionRequest
from services.engine import hosting_client, AHPEngine

logger = logging.getLogger("ahp.routes")
router = APIRouter(prefix="/sites", tags=["AHP Protocol"])

# ─── Reliability Registry URL ────────────────────────────────────────

RELIABILITY_URL = "http://localhost:7003"


async def _resolve_site(site_id: int) -> dict:
    """Resolve a site by ID from the Hosting backend."""
    site = await hosting_client.fetch_site(site_id)
    if not site:
        raise HTTPException(status_code=404, detail=f"Site {site_id} not found")
    return site


# ─── Site Discovery ────────────────────────────────────────────────────

@router.get("")
async def list_sites(
    type_filter: Optional[str] = Query(None, alias="type"),
    search: Optional[str] = Query(None, alias="q"),
):
    """List all proxied sites from the Hosting backend.

    Enriches each site with trust rating from the Reliability Registry.
    """
    sites = await hosting_client.fetch_all_sites(force=True)
    result = []

    # Fetch trust ratings map from Reliability Registry
    trust_map = await _fetch_trust_ratings()

    for site_data in sites:
        site = HostingSite(site_data)
        # Apply filters
        if type_filter and site.site_type != type_filter:
            continue
        if search and search.lower() not in site.name.lower() \
                and search.lower() not in site.description.lower():
            continue

        site_entry = {
            "id": site.id,
            "name": site.name,
            "type": site.site_type,
            "ahp_type": site.ahp_type,
            "description": site.description,
            "status": site.status,
            "capabilities": [c.get("name", "") for c in site.capabilities],
            "ahp_endpoints": {
                "agent_json": f"/sites/{site.id}",
                "info": f"/sites/{site.id}/info",
                "action": f"/sites/{site.id}/action",
                "data": f"/sites/{site.id}/data",
                "stream": f"/sites/{site.id}/stream",
            },
        }

        # Enrich with trust rating if available
        site_name = site.name.lower()
        site_id_str = str(site.id)
        
        # Match by site_id first (more reliable), then by name
        matched_trust = trust_map.get(site_id_str) or trust_map.get(site_name)
        if matched_trust:
            site_entry["trust_rating"] = matched_trust["rating"]
            site_entry["trust_score"] = matched_trust["score"]
        else:
            site_entry["trust_rating"] = "unrated"
            site_entry["trust_score"] = 0.0

        result.append(site_entry)

    return {
        "protocol": "ahp/0.1",
        "success": True,
        "total": len(result),
        "sites": result,
    }


async def _fetch_trust_ratings() -> dict[str, dict]:
    """Fetch trust ratings from the Reliability Registry.

    Returns a dict mapping site_name (lowercase) → {"rating", "score"}.
    """
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{RELIABILITY_URL}/api/leaderboard")
            if resp.status_code == 200:
                data = resp.json()
                leaderboard = data.get("leaderboard", [])
                trust_map = {}
                for entry in leaderboard:
                    name = entry.get("name", "").lower()
                    site_id = entry.get("site_id", "").lower()
                    if site_id:
                        trust_map[site_id] = {
                            "rating": entry.get("rating", "D"),
                            "score": entry.get("score", 0.0),
                        }
                    if name:
                        trust_map[name] = {
                            "rating": entry.get("rating", "D"),
                            "score": entry.get("score", 0),
                        }
                return trust_map
    except Exception as e:
        logger.debug(f"Could not fetch trust ratings: {e}")
    return {}


# ─── AHP Endpoints ─────────────────────────────────────────────────────

@router.get("/{site_id}")
async def get_agent_json(site_id: int):
    """Get agent.json for a site (AHP v0.1 compliant)."""
    site_data = await _resolve_site(site_id)
    site = HostingSite(site_data)
    return site.to_agent_json()


@router.get("/{site_id}/info")
async def get_site_info(site_id: int):
    """Get AHP Info for a site — capabilities, pricing, version."""
    site_data = await _resolve_site(site_id)
    site = HostingSite(site_data)
    info = AHPInfo(site)
    return info.to_dict()


@router.post("/{site_id}/action")
async def execute_action(site_id: int, body: dict):
    """Execute a capability on a site.

    Request body:
    ```json
    {
        "action": "analyze",
        "data": {
            "texts": ["..."],
            "type": "insight"
        }
    }
    ```
    """
    site_data = await _resolve_site(site_id)
    action_req = AHPActionRequest(body)

    if not action_req.is_valid():
        raise HTTPException(status_code=400, detail="action or type is required")

    result = await AHPEngine.execute_action(
        site_data, action_req.action, action_req.data
    )
    return result


@router.post("/{site_id}/data")
async def get_site_data(site_id: int, body: dict = {}):
    """Get data from a site with optional filters."""
    site_data = await _resolve_site(site_id)
    filters = body.get("filters", {})
    result = await AHPEngine.get_site_data(site_data, filters)
    return result


@router.get("/{site_id}/stream")
async def stream_action(site_id: int,
                        action: str = Query(""),
                        type: str = Query(""),
                        data: str = Query("")):
    """SSE stream for action execution.

    Query params (for GET-based streaming):
    - action: action name
    - type: action type (insight/extract)
    - data: JSON-encoded data payload
    """
    site_data = await _resolve_site(site_id)

    action_data = {}
    if data:
        try:
            action_data = json.loads(data)
        except json.JSONDecodeError:
            pass
    if type:
        action_data["type"] = type

    return StreamingResponse(
        AHPEngine.stream_action(site_data, action or "query", action_data),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
