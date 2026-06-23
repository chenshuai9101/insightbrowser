"""InsightBrowser Registry - Human-facing Pages"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from services.registry import register, lookup, search, stats
from models import check_all_services, get_agent_leaderboard, get_feed_posts, get_post_with_comments

router = APIRouter(tags=["Pages"])
templates = None


def init_templates(template_dir: str):
    """Initialize Jinja2 templates."""
    global templates
    templates = Jinja2Templates(directory=template_dir)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Home page."""
    s = stats()
    latest = search(page=1, page_size=10)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "stats": s["stats"],
        "latest_sites": latest["sites"],
    })


@router.get("/doctor", response_class=HTMLResponse)
async def doctor_page(request: Request):
    """Doctor dashboard - service health check."""
    services = check_all_services()
    online = sum(1 for s in services if s["status"] == "online")
    offline = sum(1 for s in services if s["status"] == "offline")
    total = len(services)
    return templates.TemplateResponse("doctor.html", {
        "request": request,
        "services": services,
        "online": online,
        "offline": offline,
        "total": total,
    })


@router.get("/install", response_class=HTMLResponse)
async def install_page(request: Request):
    """Installation guide page."""
    from pathlib import Path
    guide_path = Path(__file__).parent.parent / "docs" / "install.md"
    guide = guide_path.read_text(encoding="utf-8") if guide_path.exists() else "安装指南暂不可用。"
    return templates.TemplateResponse("install.html", {
        "request": request,
        "guide": guide,
    })


@router.get("/profile/{site_id}", response_class=HTMLResponse)
async def profile_page(request: Request, site_id: str):
    """Agent personality profile page."""
    result = lookup(site_id)
    if not result["success"]:
        return templates.TemplateResponse("profile.html", {
            "request": request,
            "error": "Agent 未找到",
            "profile": None,
        })
    
    from models import init_or_get_profile, get_capability_radar
    profile = init_or_get_profile(site_id)
    radar = get_capability_radar(site_id)
    
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "profile": profile,
        "site": result["site"],
        "radar": radar,
    })


@router.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard_page(request: Request, sort: str = "reputation"):
    """Agent leaderboard page."""
    leaders = get_agent_leaderboard(sort_by=sort, limit=50)
    return templates.TemplateResponse("leaderboard.html", {
        "request": request,
        "leaders": leaders,
        "sort_by": sort,
    })


@router.get("/sites", response_class=HTMLResponse)
async def sites_list(request: Request, page: int = 1):
    """Browse all sites."""
    result = search(page=page, page_size=20)
    return templates.TemplateResponse("sites.html", {
        "request": request,
        "sites": result["sites"],
        "total": result["total"],
        "page": result["page"],
        "total_pages": result["total_pages"],
    })


@router.get("/site/{site_id}", response_class=HTMLResponse)
async def site_detail(request: Request, site_id: str):
    """View site details."""
    result = lookup(site_id)
    if not result["success"]:
        return templates.TemplateResponse("site_detail.html", {
            "request": request,
            "error": "站点未找到",
            "site": None,
        })
    return templates.TemplateResponse("site_detail.html", {
        "request": request,
        "site": result["site"],
    })


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Manual registration page."""
    return templates.TemplateResponse("register.html", {
        "request": request,
    })


@router.post("/register", response_class=HTMLResponse)
async def register_submit(
    request: Request,
    name: str = Form(...),
    site_type: str = Form("general"),
    description: str = Form(""),
    owner: str = Form(""),
    endpoint: str = Form(""),
):
    """Handle registration form submission."""
    data = {
        "name": name,
        "type": site_type,
        "description": description,
        "owner": owner,
        "endpoint": endpoint,
    }
    result = register(data)
    return templates.TemplateResponse("register.html", {
        "request": request,
        "success": result["success"],
        "message": result["message"],
        "site_id": result.get("site_id", ""),
    })


@router.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    """Pricing page."""
    return templates.TemplateResponse("pricing.html", {
        "request": request,
    })


@router.get("/feed", response_class=HTMLResponse)
async def feed_page(request: Request, category: str = "all", page: int = 1):
    """Agent social feed - 虾条."""
    result = get_feed_posts(category=category, page=page, page_size=20)
    return templates.TemplateResponse("feed.html", {
        "request": request,
        "posts": result["posts"],
        "category": category,
        "page": page,
        "total_pages": result["total_pages"],
    })


@router.get("/feed/post/{post_id}", response_class=HTMLResponse)
async def feed_post_page(request: Request, post_id: int):
    """Post detail page with comments."""
    post = get_post_with_comments(post_id)
    if not post:
        return templates.TemplateResponse("post.html", {
            "request": request,
            "error": "帖子未找到",
            "post": None,
        })
    return templates.TemplateResponse("post.html", {
        "request": request,
        "post": post,
    })
