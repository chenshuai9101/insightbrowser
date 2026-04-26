"""InsightBrowser Reliability — Agent Rating Calculation

Computes trust ratings based on:
- Up-time percentage (α weight = 0.4)
- Success rate (β weight = 0.4)
- Activity freshness (γ weight = 0.2)

Rating scale:
- S: up_time ≥ 99.9% + success_rate ≥ 99%
- A: up_time ≥ 99%  + success_rate ≥ 95%
- B: up_time ≥ 95%  + success_rate ≥ 90%
- C: up_time ≥ 80%  + success_rate ≥ 80%
- D: other
"""
import logging
from typing import Optional

from models import get_conn, SiteRecord

logger = logging.getLogger("reliability.rating")

# ─── Default weight ──────────────────────────────────────────────────

ALPHA = 0.4   # Up-time weight
BETA = 0.4    # Success rate weight
GAMMA = 0.2   # Activity freshness weight


# ─── Rating Calculation ──────────────────────────────────────────────

def compute_rating(site_id: str) -> dict:
    """Compute trust rating for a site.

    Returns a dict with rating, score, and breakdown statistics.
    """
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM sites WHERE site_id = ?", (site_id,)
    ).fetchone()

    if not row:
        return {
            "site_id": site_id,
            "rating": "D",
            "score": 0.0,
            "up_time": 0.0,
            "success_rate": 0.0,
            "activity": 0.0,
            "total_calls": 0,
            "error": "Site not tracked",
        }

    site = SiteRecord(row)

    # ── Up-time from heartbeats ───────────────────────────────────────
    up_time = _compute_up_time(site_id)

    # ── Success rate ──────────────────────────────────────────────────
    success_rate = _compute_success_rate(site)

    # ── Activity freshness ────────────────────────────────────────────
    activity = _compute_activity(site_id, site)

    # ── Composite score ──────────────────────────────────────────────
    score = round(ALPHA * up_time + BETA * success_rate + GAMMA * activity, 4)

    # ── Letter rating ─────────────────────────────────────────────────
    rating_letter = _letter_rating(up_time, success_rate)

    return {
        "site_id": site_id,
        "name": site.name,
        "rating": rating_letter,
        "score": score,
        "up_time": round(up_time * 100, 2),
        "success_rate": round(success_rate * 100, 2),
        "activity": round(activity * 100, 2),
        "total_calls": site.total_calls,
        "successful_calls": site.successful_calls,
        "failed_calls": site.failed_calls,
    }


def compute_all_ratings() -> list[dict]:
    """Compute ratings for all tracked sites."""
    conn = get_conn()
    rows = conn.execute("SELECT site_id FROM sites").fetchall()
    ratings = []
    for row in rows:
        try:
            ratings.append(compute_rating(row["site_id"]))
        except Exception as e:
            logger.warning(f"Rating error for {row['site_id']}: {e}")
    return ratings


def _compute_up_time(site_id: str) -> float:
    """Compute up-time ratio from last 24 hours of heartbeats."""
    conn = get_conn()
    # Get heartbeats from last 24h
    rows = conn.execute(
        """SELECT status FROM heartbeats
           WHERE site_id = ? AND checked_at >= datetime('now', '-1 day')
           ORDER BY checked_at DESC LIMIT 500""",
        (site_id,),
    ).fetchall()

    if not rows:
        return 0.0

    total = len(rows)
    alive = sum(1 for r in rows if r["status"] == "alive")
    return alive / total if total > 0 else 0.0


def _compute_success_rate(site: SiteRecord) -> float:
    """Compute call success rate."""
    total = site.total_calls
    if total == 0:
        return 0.0
    return site.successful_calls / total


def _compute_activity(site_id: str, site: SiteRecord) -> float:
    """Compute activity freshness score (0.0 - 1.0).

    Higher = more recently active. Decays over 7 days.
    """
    if not site.last_seen:
        return 0.0

    import datetime
    try:
        last = datetime.datetime.fromisoformat(site.last_seen)
        now = datetime.datetime.utcnow()
        # Also try to convert 'now' to the same tz awareness
        if last.tzinfo:
            now = now.replace(tzinfo=last.tzinfo)

        delta = (now - last).total_seconds() / 86400  # in days
        if delta < 0:
            return 1.0
        # Decay from 1.0 → 0.0 over 7 days
        return max(0.0, 1.0 - (delta / 7.0))
    except Exception:
        return 0.0


def _letter_rating(up_time: float, success_rate: float) -> str:
    """Map up-time and success rate to letter grade."""
    if up_time >= 0.999 and success_rate >= 0.99:
        return "S"
    elif up_time >= 0.99 and success_rate >= 0.95:
        return "A"
    elif up_time >= 0.95 and success_rate >= 0.90:
        return "B"
    elif up_time >= 0.80 and success_rate >= 0.80:
        return "C"
    else:
        return "D"
