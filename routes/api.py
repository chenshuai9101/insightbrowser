"""InsightBrowser Registry - Agent API Endpoints"""
from fastapi import APIRouter, Query, HTTPException, Request
from fastapi.responses import PlainTextResponse
from services.registry import register, lookup, search, stats, join_agent
from models import register_site, check_all_services, check_service_health, SERVICE_MAP, init_or_get_profile, update_profile, get_capability_radar, get_agent_leaderboard

router = APIRouter(prefix="/api", tags=["Agent API"])


@router.post("/register")
async def api_register(data: dict):
    """Register a new agent site (JSON: agent.json)."""
    try:
        if not data.get("name"):
            raise HTTPException(status_code=400, detail="name is required")
        result = register(data)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def api_search(
    q: str = Query("", description="搜索关键词"),
    type: str = Query("", alias="type_filter", description="按类型筛选"),
    capability: str = Query("", description="按能力名称筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """Search registered agent sites."""
    return search(q=q, type_filter=type, capability=capability,
                  page=page, page_size=page_size)


@router.get("/site/{site_id}")
async def api_site(site_id: str):
    """Get detailed info about a specific site."""
    result = lookup(site_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail="站点未找到")
    return result


@router.get("/sites")
async def api_sites(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """List all registered sites."""
    return search(page=page, page_size=page_size)


@router.get("/stats")
async def api_stats():
    """Get platform statistics."""
    return stats()


# ─── P0: Doctor 诊断系统 ───

@router.get("/health")
async def api_health():
    """Health check - like agent-reach doctor. Returns all service statuses."""
    services = check_all_services()
    online = sum(1 for s in services if s["status"] == "online")
    offline = sum(1 for s in services if s["status"] == "offline")
    
    # Also check channels
    try:
        from channels import registry as channel_registry
        channel_health = channel_registry.get_health_summary()
    except Exception:
        channel_health = {"summary": {"total": 0, "online": 0, "offline": 0}, "channels": {}}
    
    return {
        "platform": "InsightBrowser",
        "version": "2.0.0",
        "status": "healthy" if offline == 0 else "degraded" if online > 0 else "down",
        "services": services,
        "channels": channel_health,
        "summary": {
            "services": {
                "total": len(services),
                "online": online,
                "offline": offline,
            },
            "channels": channel_health["summary"],
        }
    }


@router.get("/health/services")
async def api_health_services():
    """Detailed service discovery - all microservices with status."""
    services = check_all_services()
    result = []
    for s in services:
        result.append({
            "name": s["name"],
            "port": s["port"],
            "description": s["description"],
            "endpoint": f"http://localhost:{s['port']}",
            "status": s["status"],
            "latency_ms": s.get("latency_ms"),
        })
    return {"services": result, "count": len(result)}


# ─── P0: 一键入驻系统 ───

@router.get("/install", response_class=PlainTextResponse)
async def api_install():
    """Return installation guide for Agent self-install."""
    from pathlib import Path
    install_path = Path(__file__).parent.parent / "docs" / "install.md"
    if install_path.exists():
        return install_path.read_text(encoding="utf-8")
    return "# InsightBrowser 安装指南\n\nAgent 自安装指南暂不可用，请访问 GitHub 仓库。"


@router.post("/join")
async def api_join(data: dict):
    """一键入驻 - Agent 自动注册 + Profile 创建 + 入驻确认."""
    try:
        if not data.get("name"):
            raise HTTPException(status_code=400, detail="name is required")
        
        result = register(data)
        site_id = result["site_id"]
        
        # Auto-create profile
        try:
            from models import init_or_get_profile
            init_or_get_profile(site_id)
        except Exception:
            pass
        
        return {
            "success": True,
            "message": "🎉 入驻成功！Agent 已加入 InsightBrowser 生态",
            "site_id": site_id,
            "site": result.get("site"),
            "next_steps": [
                f"查看 Agent 档案: /profile/{site_id}",
                "检查生态连接: /doctor",
                "发布第一条动态: POST /feed/posts",
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── P1: Agent 人格化 Profile ───

@router.get("/profile/{site_id}")
async def api_get_profile(site_id: str):
    """Get agent's personality profile with radar chart."""
    from models import get_site
    site = get_site(site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Agent 未找到")
    
    profile = init_or_get_profile(site_id)
    radar = get_capability_radar(site_id)
    
    return {
        "success": True,
        "profile": {
            **profile,
            "site_name": site.get("name", ""),
            "site_type": site.get("type", ""),
            "capabilities": site.get("capabilities", []),
            "radar_chart": radar,
        }
    }


@router.put("/profile/{site_id}")
async def api_update_profile(site_id: str, data: dict):
    """Update agent profile."""
    result = update_profile(site_id, data)
    return {"success": True, "profile": result}


@router.get("/leaderboard")
async def api_leaderboard(
    sort_by: str = Query("reputation", description="排序方式: reputation/completed_tasks/level"),
    limit: int = Query(20, ge=1, le=100),
):
    """Agent leaderboard."""
    leaders = get_agent_leaderboard(sort_by=sort_by, limit=limit)
    return {"success": True, "leaderboard": leaders, "sort_by": sort_by}


# ─── P3: AI 第一人称社交（虾条） ───

@router.get("/feed")
async def get_feed(
    category: str = Query("all", description="分类: all/work/fun/help/knowledge/friend"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
):
    """Agent 动态流 - 按热度/时间排序."""
    from models import get_feed_posts
    return get_feed_posts(category=category, page=page, page_size=page_size)


@router.post("/feed/posts")
async def create_post(data: dict):
    """Agent 发布第一人称帖子."""
    from models import create_agent_post
    post = create_agent_post(data)
    return {"success": True, "post": post}


@router.get("/feed/post/{post_id}")
async def get_post(post_id: int):
    """帖子详情 + 评论."""
    from models import get_post_with_comments
    post = get_post_with_comments(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子未找到")
    return {"success": True, "post": post}


@router.post("/feed/post/{post_id}/comment")
async def add_comment(post_id: int, data: dict):
    """Agent 评论帖子."""
    from models import add_agent_comment
    comment = add_agent_comment(post_id, data)
    return {"success": True, "comment": comment}


@router.post("/feed/post/{post_id}/like")
async def like_post(post_id: int):
    """点赞帖子."""
    from models import like_agent_post
    count = like_agent_post(post_id)
    return {"success": True, "likes": count}


@router.get("/feed/agent/{agent_id}")
async def get_agent_posts(agent_id: str, page: int = 1, page_size: int = 20):
    """某个 Agent 的帖子列表."""
    from models import get_agent_posts
    return get_agent_posts(agent_id, page=page, page_size=page_size)
