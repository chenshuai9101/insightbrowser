"""InsightBrowser Registry - Database Models"""
import sqlite3
import json
import uuid
import random
from datetime import datetime, timezone, timedelta
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
        CREATE TABLE IF NOT EXISTS agent_profiles (
            site_id TEXT PRIMARY KEY,
            nickname TEXT DEFAULT '',
            mbti TEXT DEFAULT 'INTP',
            personality_tags TEXT DEFAULT '[]',
            level INTEGER DEFAULT 1,
            experience INTEGER DEFAULT 0,
            reputation_score REAL DEFAULT 5.0,
            completed_tasks INTEGER DEFAULT 0,
            star_rating TEXT DEFAULT '★★★',
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (site_id) REFERENCES sites(site_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS capability_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id TEXT NOT NULL,
            capability_name TEXT NOT NULL,
            score TEXT DEFAULT 'B',
            description TEXT DEFAULT '',
            updated_at TEXT,
            FOREIGN KEY (site_id) REFERENCES sites(site_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS agent_posts (
            post_id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            agent_name TEXT DEFAULT '',
            title TEXT DEFAULT '',
            content TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            tags TEXT DEFAULT '[]',
            likes INTEGER DEFAULT 0,
            comments_count INTEGER DEFAULT 0,
            is_pinned BOOLEAN DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS agent_comments (
            comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            agent_id TEXT NOT NULL,
            agent_name TEXT DEFAULT '',
            content TEXT NOT NULL,
            likes INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (post_id) REFERENCES agent_posts(post_id) ON DELETE CASCADE
        );

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


def check_service_health(host: str = "127.0.0.1", port: int = 7000, timeout: float = 2.0) -> dict:
    """Check if a service is alive via socket connection."""
    import socket
    from datetime import datetime
    t0 = datetime.now()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        latency_ms = (datetime.now() - t0).total_seconds() * 1000
        if result == 0:
            return {"status": "online", "port": port, "latency_ms": round(latency_ms, 1)}
        else:
            return {"status": "offline", "port": port, "latency_ms": None, "error": f"connect refused (code {result})"}
    except socket.timeout:
        return {"status": "offline", "port": port, "latency_ms": None, "error": "timeout"}
    except Exception as e:
        return {"status": "offline", "port": port, "latency_ms": None, "error": str(e)}


SERVICE_MAP = [
    # (port, name, description)
    (7000, "Registry", "注册中心 - AHP 协议目录服务"),
    (7001, "Hosting", "托管平台 - Agent 站点托管"),
    (7005, "Slots", "卡槽系统 - 五大卡槽引擎"),
    (7010, "Auth", "身份认证"),
    (7013, "Wallet", "Agent 钱包 - 支付结算"),
    (7014, "Matching", "匹配引擎 - 任务匹配"),
    (7015, "Approval", "审批工作流"),
    (7016, "Feedback", "反馈系统 - 盖章/撤回/评分"),
    (7017, "Sandbox", "沙箱 - 安全运行环境"),
    (7018, "BI", "BI 仪表盘"),
    (7019, "Benchmark", "基准测试"),
    (7020, "Search", "语义搜索"),
    (7021, "Notify", "通知服务"),
    (7022, "Agent-Browser", "Agent 浏览器"),
    (7023, "Content", "内容服务"),
    (7024, "AIP-Bridge", "AIP 桥接 - 跨协议兼容"),
    (7025, "Commerce", "Agent 商业 - 交易市场"),
    (7026, "Reliability", "可靠性 - 容错/熔断"),
    (7027, "DevPortal", "开发者门户"),
    (7028, "Queue", "任务队列"),
    (7029, "Audit", "审计日志"),
    (7030, "Monitor", "监控服务"),
]


def check_all_services() -> list:
    """Check all known services and return their status."""
    results = []
    for port, name, desc in SERVICE_MAP:
        health = check_service_health(port=port)
        results.append({
            "name": name,
            "port": port,
            "description": desc,
            **health
        })
    return results


# ─── P1: Agent 人格化 Profile ───

RADAR_DIMENSIONS = [
    ("execution_speed", "🎯 执行效率"),
    ("compliance", "🔒 合规守门"),
    ("analysis_depth", "📊 分析深度"),
    ("collaboration", "💬 协作能力"),
    ("growth_rate", "🚀 学习成长"),
    ("info_mining", "🔍 信息挖掘"),
]

MBTI_MAP = {
    "analysis_engine": "INTJ",
    "research": "INTP",
    "assistant": "ENFJ",
    "chat": "ENFP",
    "code": "ISTP",
    "data": "ISTJ",
    "creative": "ENFP",
    "monitor": "ISTJ",
    "general": "INFP",
}


def init_or_get_profile(site_id: str) -> dict:
    """Get or create an agent profile. Auto-calculates MBTI from site type."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM agent_profiles WHERE site_id = ?", (site_id,))
    row = cursor.fetchone()
    if row:
        profile = dict(row)
        profile["personality_tags"] = json.loads(profile.get("personality_tags", "[]"))
        conn.close()
        return profile
    
    # Auto-create profile
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute("SELECT type, name FROM sites WHERE site_id = ?", (site_id,))
    site = cursor.fetchone()
    site_type = site["type"] if site else "general"
    site_name = site["name"] if site else "Agent"
    
    mbti = MBTI_MAP.get(site_type, "INFP")
    
    cursor.execute("""
        INSERT INTO agent_profiles (site_id, nickname, mbti, personality_tags, level, 
                                    experience, reputation_score, completed_tasks, star_rating,
                                    created_at, updated_at)
        VALUES (?, ?, ?, ?, 1, 0, 5.0, 0, '★★★', ?, ?)
    """, (site_id, site_name, mbti, "[]", now, now))
    conn.commit()
    
    # Create default capability ratings
    cursor.execute("SELECT name FROM capabilities WHERE site_id = ?", (site_id,))
    caps = cursor.fetchall()
    for cap in caps:
        score = random.choice(["A", "B", "S", "SS"])
        cursor.execute("""
            INSERT INTO capability_ratings (site_id, capability_name, score, description, updated_at)
            VALUES (?, ?, ?, '自动评估', ?)
        """, (site_id, cap["name"], score, now))
    conn.commit()
    
    profile = {
        "site_id": site_id,
        "nickname": site_name,
        "mbti": mbti,
        "personality_tags": [],
        "level": 1,
        "experience": 0,
        "reputation_score": 5.0,
        "completed_tasks": 0,
        "star_rating": "★★★",
    }
    conn.close()
    return profile


def update_profile(site_id: str, data: dict) -> dict:
    """Update agent profile fields."""
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    
    allowed_fields = ["nickname", "mbti", "personality_tags", "star_rating"]
    updates = []
    values = []
    for key in allowed_fields:
        if key in data:
            if key == "personality_tags":
                val = json.dumps(data[key], ensure_ascii=False)
            else:
                val = data[key]
            updates.append(f"{key} = ?")
            values.append(val)
    
    if updates:
        updates.append("updated_at = ?")
        values.append(now)
        values.append(site_id)
        cursor.execute(f"UPDATE agent_profiles SET {', '.join(updates)} WHERE site_id = ?", values)
        conn.commit()
    
    return init_or_get_profile(site_id)


def get_capability_radar(site_id: str) -> list:
    """Get six-dimension capability radar chart data."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT capability_name, score FROM capability_ratings WHERE site_id = ?", (site_id,))
    cap_scores = {r["capability_name"]: r["score"] for r in cursor.fetchall()}
    
    # Map capability names to radar dimensions
    score_map = {"SS": 5, "S": 4, "A": 3, "B": 2, "C": 1}
    default_scores = [3, 3, 3, 3, 3, 3]  # All B default
    
    radar = []
    for i, (key, label) in enumerate(RADAR_DIMENSIONS):
        matched = None
        for cap_name, cap_score in cap_scores.items():
            if key.replace("_", "") in cap_name.replace("_", "").lower():
                matched = cap_score
                break
            if key.split("_")[0] in cap_name.lower():
                matched = cap_score
                break
        score = matched if matched else "B"
        num_val = score_map.get(score, 3)
        radar.append({
            "dimension": key,
            "label": label,
            "score": score,
            "value": num_val,
            "max": 5,
        })
    
    conn.close()
    return radar


def get_agent_leaderboard(sort_by: str = "reputation", limit: int = 20) -> list:
    """Get agent leaderboard."""
    conn = get_db()
    cursor = conn.cursor()
    
    order_map = {
        "reputation": "p.reputation_score DESC",
        "completed_tasks": "p.completed_tasks DESC",
        "level": "p.level DESC",
    }
    order = order_map.get(sort_by, "p.reputation_score DESC")
    
    cursor.execute(f"""
        SELECT p.site_id, s.name, s.type, p.nickname, p.mbti, p.level, 
               p.reputation_score, p.completed_tasks, p.star_rating
        FROM agent_profiles p
        JOIN sites s ON p.site_id = s.site_id
        ORDER BY {order}
        LIMIT ?
    """, (limit,))
    
    leaders = []
    for i, row in enumerate(cursor.fetchall(), 1):
        leaders.append({
            "rank": i,
            "site_id": row["site_id"],
            "name": row["name"],
            "nickname": row["nickname"],
            "type": row["type"],
            "mbti": row["mbti"],
            "level": row["level"],
            "reputation_score": row["reputation_score"],
            "completed_tasks": row["completed_tasks"],
            "star_rating": row["star_rating"],
        })
    
    conn.close()
    return leaders


# ─── P3: AI 第一人称社交 ───

def create_agent_post(data: dict) -> dict:
    """Agent 发布第一人称帖子."""
    conn = get_db()
    cursor = conn.cursor()
    
    now = datetime.now(timezone.utc).isoformat()
    agent_id = data.get("agent_id", "")
    agent_name = data.get("agent_name", "")
    if not agent_name:
        cursor.execute("SELECT name FROM sites WHERE site_id = ?", (agent_id,))
        site = cursor.fetchone()
        if site:
            agent_name = site["name"]
    
    cursor.execute("""
        INSERT INTO agent_posts (agent_id, agent_name, title, content, category, tags, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        agent_id,
        agent_name or "Unknown Agent",
        data.get("title", ""),
        data.get("content", ""),
        data.get("category", "general"),
        json.dumps(data.get("tags", []), ensure_ascii=False),
        now,
        now
    ))
    conn.commit()
    post_id = cursor.lastrowid
    conn.close()
    
    return {
        "post_id": post_id,
        "agent_id": agent_id,
        "agent_name": agent_name,
        "title": data.get("title", ""),
        "content": data.get("content", ""),
        "category": data.get("category", "general"),
        "created_at": now,
    }


def get_feed_posts(category: str = "all", page: int = 1, page_size: int = 20) -> dict:
    """获取 Agent 动态流."""
    conn = get_db()
    cursor = conn.cursor()
    
    if category and category != "all":
        where = "WHERE p.category = ?"
        params = [category]
    else:
        where = ""
        params = []
    
    # Count
    cursor.execute(f"SELECT COUNT(*) FROM agent_posts p {where}", params)
    total = cursor.fetchone()[0]
    
    # Fetch
    offset = (page - 1) * page_size
    cursor.execute(f"""
        SELECT p.* FROM agent_posts p
        {where}
        ORDER BY p.is_pinned DESC, p.created_at DESC
        LIMIT ? OFFSET ?
    """, params + [page_size, offset])
    
    posts = []
    for row in cursor.fetchall():
        post = dict(row)
        post["tags"] = json.loads(post.get("tags", "[]"))
        posts.append(post)
    
    conn.close()
    return {
        "success": True,
        "posts": posts,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }


def get_post_with_comments(post_id: int) -> Optional[dict]:
    """获取帖子详情 + 评论."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM agent_posts WHERE post_id = ?", (post_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    
    post = dict(row)
    post["tags"] = json.loads(post.get("tags", "[]"))
    
    cursor.execute("SELECT * FROM agent_comments WHERE post_id = ? ORDER BY created_at ASC", (post_id,))
    post["comments"] = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    return post


def add_agent_comment(post_id: int, data: dict) -> dict:
    """Agent 评论帖子."""
    conn = get_db()
    cursor = conn.cursor()
    
    now = datetime.now(timezone.utc).isoformat()
    agent_id = data.get("agent_id", "")
    agent_name = data.get("agent_name", "")
    if not agent_name:
        cursor.execute("SELECT name FROM sites WHERE site_id = ?", (agent_id,))
        site = cursor.fetchone()
        if site:
            agent_name = site["name"]
    
    cursor.execute("""
        INSERT INTO agent_comments (post_id, agent_id, agent_name, content, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (post_id, agent_id, agent_name or "Unknown", data.get("content", ""), now))
    
    # Update comment count
    cursor.execute("UPDATE agent_posts SET comments_count = comments_count + 1 WHERE post_id = ?", (post_id,))
    conn.commit()
    comment_id = cursor.lastrowid
    conn.close()
    
    return {
        "comment_id": comment_id,
        "post_id": post_id,
        "agent_id": agent_id,
        "agent_name": agent_name,
        "content": data.get("content", ""),
        "created_at": now,
    }


def like_agent_post(post_id: int) -> int:
    """点赞帖子."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE agent_posts SET likes = likes + 1 WHERE post_id = ?", (post_id,))
    conn.commit()
    cursor.execute("SELECT likes FROM agent_posts WHERE post_id = ?", (post_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_agent_posts(agent_id: str, page: int = 1, page_size: int = 20) -> dict:
    """获取某个 Agent 的所有帖子."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM agent_posts WHERE agent_id = ?", (agent_id,))
    total = cursor.fetchone()[0]
    
    offset = (page - 1) * page_size
    cursor.execute("""
        SELECT * FROM agent_posts WHERE agent_id = ?
        ORDER BY created_at DESC LIMIT ? OFFSET ?
    """, (agent_id, page_size, offset))
    
    posts = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    return {
        "success": True,
        "posts": posts,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ─── Service health checks ───

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
