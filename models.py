"""InsightBrowser Registry - Database Models"""
import sqlite3
import json
import uuid
from datetime import datetime, timezone
from typing import Optional
from config import DATABASE_URL
import os


def get_db():
    """Get a database connection."""
    os.makedirs(os.path.dirname(DATABASE_URL), exist_ok=True)
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS sites (
            site_id TEXT PRIMARY KEY,
            protocol TEXT NOT NULL DEFAULT 'ahp/0.1',
            name TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'general',
            description TEXT DEFAULT '',
            owner TEXT DEFAULT '',
            endpoint TEXT DEFAULT '',
            trust_level TEXT DEFAULT 'unverified',
            rating REAL DEFAULT 0.0,
            usage_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS capabilities (
            id TEXT NOT NULL,
            site_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            params TEXT DEFAULT '{}',
            returns TEXT DEFAULT '{}',
            PRIMARY KEY (id, site_id),
            FOREIGN KEY (site_id) REFERENCES sites(site_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_sites_type ON sites(type);
        CREATE INDEX IF NOT EXISTS idx_sites_name ON sites(name);
        CREATE INDEX IF NOT EXISTS idx_capabilities_name ON capabilities(name);
        CREATE INDEX IF NOT EXISTS idx_capabilities_site ON capabilities(site_id);
    """)
    conn.commit()
    conn.close()


def generate_site_id() -> str:
    """Generate a unique site ID."""
    return f"site_{uuid.uuid4().hex[:12]}"


def register_site(data: dict) -> dict:
    """Register a new agent site with its capabilities."""
    conn = get_db()
    cursor = conn.cursor()

    now = datetime.now(timezone.utc).isoformat()
    site_id = generate_site_id()

    site_data = {
        "site_id": site_id,
        "protocol": data.get("protocol", "ahp/0.1"),
        "name": data.get("name", "Unnamed Site"),
        "type": data.get("type", "general"),
        "description": data.get("description", ""),
        "owner": data.get("owner", ""),
        "endpoint": data.get("endpoint", ""),
        "trust_level": data.get("trust_level", "unverified"),
        "rating": float(data.get("rating", 0.0)),
        "usage_count": int(data.get("usage_count", 0)),
        "created_at": now,
        "updated_at": now,
    }

    cursor.execute("""
        INSERT INTO sites (site_id, protocol, name, type, description, owner,
                          endpoint, trust_level, rating, usage_count,
                          created_at, updated_at)
        VALUES (:site_id, :protocol, :name, :type, :description, :owner,
                :endpoint, :trust_level, :rating, :usage_count,
                :created_at, :updated_at)
    """, site_data)

    capabilities = data.get("capabilities", [])
    for cap in capabilities:
        cap_id = cap.get("id", f"cap_{uuid.uuid4().hex[:8]}")
        cursor.execute("""
            INSERT INTO capabilities (id, site_id, name, description, params, returns)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            cap_id,
            site_id,
            cap.get("name", ""),
            cap.get("description", ""),
            json.dumps(cap.get("params", {}), ensure_ascii=False),
            json.dumps(cap.get("returns", {}), ensure_ascii=False),
        ))

    conn.commit()
    conn.close()

    return site_data


def get_site(site_id: str) -> Optional[dict]:
    """Get a site by ID with its capabilities."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sites WHERE site_id = ?", (site_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    site = dict(row)
    cursor.execute("SELECT * FROM capabilities WHERE site_id = ?", (site_id,))
    caps = []
    for cap_row in cursor.fetchall():
        cap = dict(cap_row)
        cap["params"] = json.loads(cap["params"])
        cap["returns"] = json.loads(cap["returns"])
        caps.append(cap)

    site["capabilities"] = caps
    conn.close()
    return site


def search_sites(query: str = "", type_filter: str = "",
                 capability: str = "", page: int = 1,
                 page_size: int = 20) -> dict:
    """Search sites by query, type, or capability."""
    conn = get_db()
    cursor = conn.cursor()

    conditions = []
    params = []

    if query:
        conditions.append("(s.name LIKE ? OR s.description LIKE ?)")
        params.extend([f"%{query}%", f"%{query}%"])

    if type_filter:
        conditions.append("s.type = ?")
        params.append(type_filter)

    if capability:
        conditions.append("EXISTS (SELECT 1 FROM capabilities c WHERE c.site_id = s.site_id AND c.name LIKE ?)")
        params.append(f"%{capability}%")

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Count total
    cursor.execute(f"SELECT COUNT(*) FROM sites s WHERE {where_clause}", params)
    total = cursor.fetchone()[0]

    # Fetch page
    offset = (page - 1) * page_size
    cursor.execute(f"""
        SELECT s.* FROM sites s
        WHERE {where_clause}
        ORDER BY s.created_at DESC
        LIMIT ? OFFSET ?
    """, params + [page_size, offset])

    sites = []
    for row in cursor.fetchall():
        site = dict(row)
        cursor.execute("SELECT * FROM capabilities WHERE site_id = ?", (site["site_id"],))
        caps = []
        for cap_row in cursor.fetchall():
            cap = dict(cap_row)
            cap["params"] = json.loads(cap["params"])
            cap["returns"] = json.loads(cap["returns"])
            caps.append(cap)
        site["capabilities"] = caps
        sites.append(site)

    conn.close()
    return {
        "sites": sites,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }


def list_all_sites(page: int = 1, page_size: int = 20) -> dict:
    """List all registered sites with pagination."""
    return search_sites(page=page, page_size=page_size)


def get_stats() -> dict:
    """Get platform statistics."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM sites")
    total_sites = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM capabilities")
    total_capabilities = cursor.fetchone()[0]

    cursor.execute("SELECT type, COUNT(*) as cnt FROM sites GROUP BY type ORDER BY cnt DESC")
    types = [{"type": r["type"], "count": r["cnt"]} for r in cursor.fetchall()]

    cursor.execute("SELECT trust_level, COUNT(*) as cnt FROM sites GROUP BY trust_level")
    trust_levels = {r["trust_level"]: r["cnt"] for r in cursor.fetchall()}

    cursor.execute("SELECT name, COUNT(*) as cnt FROM capabilities GROUP BY name ORDER BY cnt DESC LIMIT 10")
    top_capabilities = [{"name": r["name"], "count": r["cnt"]} for r in cursor.fetchall()]

    conn.close()
    return {
        "total_sites": total_sites,
        "total_capabilities": total_capabilities,
        "site_types": types,
        "trust_levels": trust_levels,
        "top_capabilities": top_capabilities,
    }
