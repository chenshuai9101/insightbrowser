"""InsightBrowser Reliability — Trust & Rating API Routes

Endpoints:
- GET  /api/trust/{site_id}     → Trust report for a site
- GET  /api/stats               → Global statistics
- GET  /api/leaderboard         → Site trust leaderboard
- POST /api/heartbeat/{site_id} → Manual heartbeat trigger
- GET  /api/dashboard           → Management dashboard JSON
- GET  /api/health              → Service health check
"""
import logging

from fastapi import APIRouter, HTTPException, Query

from models import get_conn, SiteRecord
from services.rating import compute_rating, compute_all_ratings
from services.heartbeater import heartbeater

logger = logging.getLogger("reliability.routes.trust")
router = APIRouter(prefix="/api", tags=["Trust & Ratings"])


# ─── Trust Report ──────────────────────────────────────────────────────

@router.get("/trust/{site_id}")
async def get_trust_report(site_id: str):
    """Get a detailed trust report for a site.

    Includes rating, up-time, success rate, and call volume.
    """
    rating = compute_rating(site_id)
    return {
        "success": True,
        "trust_report": rating,
    }


# ─── Global Statistics ─────────────────────────────────────────────────

@router.get("/stats")
async def get_global_stats():
    """Get global reliability statistics across all tracked sites."""
    conn = get_conn()

    # Total sites tracked
    total_sites = conn.execute("SELECT COUNT(*) as c FROM sites").fetchone()["c"]

    # Total heartbeats recorded
    total_heartbeats = conn.execute(
        "SELECT COUNT(*) as c FROM heartbeats"
    ).fetchone()["c"]

    # Recent heartbeats (last 5 min)
    recent_alive = conn.execute(
        """SELECT COUNT(*) as c FROM heartbeats
           WHERE status = 'alive' AND checked_at >= datetime('now', '-5 minutes')"""
    ).fetchone()["c"]
    recent_dead = conn.execute(
        """SELECT COUNT(*) as c FROM heartbeats
           WHERE status = 'dead' AND checked_at >= datetime('now', '-5 minutes')"""
    ).fetchone()["c"]

    # Total transactions
    total_tx = conn.execute(
        "SELECT COUNT(*) as c FROM transactions"
    ).fetchone()["c"]

    # Total credits in system
    total_balance = conn.execute(
        "SELECT COALESCE(SUM(balance), 0) as s FROM agent_accounts"
    ).fetchone()["s"]

    # Ratings distribution
    ratings = compute_all_ratings()
    rating_dist = {"S": 0, "A": 0, "B": 0, "C": 0, "D": 0}
    for r in ratings:
        letter = r.get("rating", "D")
        rating_dist[letter] = rating_dist.get(letter, 0) + 1

    return {
        "success": True,
        "stats": {
            "total_tracked_sites": total_sites,
            "total_heartbeats": total_heartbeats,
            "recent_alive": recent_alive,
            "recent_dead": recent_dead,
            "total_transactions": total_tx,
            "total_credits_in_system": total_balance,
            "rating_distribution": rating_dist,
        },
    }


# ─── Leaderboard ───────────────────────────────────────────────────────

@router.get("/leaderboard")
async def get_leaderboard(
    limit: int = Query(20, ge=1, le=100),
    min_rating: str = Query("", description="Minimum rating filter (S/A/B/C/D)"),
):
    """Get site trust leaderboard, sorted by score."""
    ratings = compute_all_ratings()

    # Filter by minimum rating
    rating_order = {"S": 0, "A": 1, "B": 2, "C": 3, "D": 4}
    if min_rating and min_rating.upper() in rating_order:
        min_order = rating_order[min_rating.upper()]
        ratings = [
            r for r in ratings
            if rating_order.get(r.get("rating", "D"), 4) >= min_order
        ]

    # Sort by composite score descending
    ratings.sort(key=lambda r: r.get("score", 0), reverse=True)

    return {
        "success": True,
        "total": len(ratings),
        "leaderboard": ratings[:limit],
    }


# ─── Manual Heartbeat ─────────────────────────────────────────────────

@router.post("/heartbeat/{site_id}")
async def trigger_heartbeat(site_id: str):
    """Manually trigger a heartbeat check for a specific site.

    Used for on-demand health checks (e.g., via AHP Proxy callback).
    """
    try:
        result = await heartbeater.ping_site_by_id(site_id)
        return {
            "success": True,
            "heartbeat": result,
        }
    except Exception as e:
        logger.error("Manual heartbeat failed for %s: %s", site_id, e)
        raise HTTPException(status_code=500, detail=str(e))


# ─── Dashboard ─────────────────────────────────────────────────────────

@router.get("/dashboard")
async def get_dashboard():
    """Get comprehensive management dashboard data.

    Returns:
    - Global stats summary
    - Rating distribution
    - Trust leaderboard (top 10)
    - Recent transactions (last 10)
    """
    conn = get_conn()

    # Stats
    total_sites = conn.execute("SELECT COUNT(*) as c FROM sites").fetchone()["c"]
    total_heartbeats = conn.execute(
        "SELECT COUNT(*) as c FROM heartbeats"
    ).fetchone()["c"]
    total_tx = conn.execute(
        "SELECT COUNT(*) as c FROM transactions"
    ).fetchone()["c"]
    total_balance = conn.execute(
        "SELECT COALESCE(SUM(balance), 0) as s FROM agent_accounts"
    ).fetchone()["s"]

    # Ratings
    ratings = compute_all_ratings()
    rating_dist = {"S": 0, "A": 0, "B": 0, "C": 0, "D": 0}
    for r in ratings:
        rating_dist[r.get("rating", "D")] = rating_dist.get(r.get("rating", "D"), 0) + 1

    # Top 10 leaderboard
    ratings.sort(key=lambda r: r.get("score", 0), reverse=True)
    top_sites = ratings[:10]

    # Recent transactions
    tx_rows = conn.execute(
        "SELECT * FROM transactions ORDER BY timestamp DESC LIMIT 10"
    ).fetchall()
    recent_tx = [
        {
            "from_agent": r["from_agent"],
            "to_agent": r["to_agent"],
            "site_id": r["site_id"],
            "credit_cost": r["credit_cost"],
            "success": bool(r["success"]),
            "timestamp": r["timestamp"],
        }
        for r in tx_rows
    ]

    return {
        "success": True,
        "dashboard": {
            "summary": {
                "total_tracked_sites": total_sites,
                "total_heartbeats": total_heartbeats,
                "total_transactions": total_tx,
                "total_credits": total_balance,
            },
            "rating_distribution": rating_dist,
            "top_sites": top_sites,
            "recent_transactions": recent_tx,
        },
    }


# ─── Health Check ──────────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "reliability-registry"}
