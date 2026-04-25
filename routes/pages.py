"""InsightBrowser Registry - Human-facing Pages"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from services.registry import register, lookup, search, stats

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
