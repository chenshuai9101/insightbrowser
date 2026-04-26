"""Commerce Bridge - Page Routes (Jinja2 frontend)

Renders the merchant onboarding form UI.
"""
import logging
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger("commerce.pages")

router = APIRouter(tags=["Pages"])

# ─── Template Setup ──────────────────────────────────────────────────

_templates_dir = Path(__file__).resolve().parent.parent / "templates"
template_env = Environment(
    loader=FileSystemLoader(str(_templates_dir)),
    autoescape=True,
)

def render(template_name: str, context: dict) -> HTMLResponse:
    template = template_env.get_template(template_name)
    html = template.render(**context)
    return HTMLResponse(content=html)


# ─── Product Categories ──────────────────────────────────────────────

CATEGORIES = [
    {"id": "手机", "name": "📱 手机数码"},
    {"id": "家电", "name": "🏠 家用电器"},
    {"id": "餐饮", "name": "🍜 餐饮美食"},
    {"id": "教育", "name": "📚 教育培训"},
    {"id": "金融", "name": "🏦 金融服务"},
    {"id": "服装", "name": "👗 服装服饰"},
    {"id": "美妆", "name": "💄 美妆个护"},
    {"id": "母婴", "name": "👶 母婴用品"},
    {"id": "家居", "name": "🛋️ 家居生活"},
    {"id": "其他", "name": "📦 其他"},
]


# ─── Routes ──────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the merchant onboarding form."""
    return render("index.html", {
        "request": request,
        "categories": CATEGORIES,
    })
