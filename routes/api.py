"""InsightBrowser Registry - Agent API Endpoints"""
from fastapi import APIRouter, Query, HTTPException
from services.registry import register, lookup, search, stats
from models import register_site

router = APIRouter(prefix="/api", tags=["Agent API"])


@router.post("/register")
async def api_register(data: dict):
    """Register a new agent site (JSON: agent.json)."""
    try:
        # Validate required fields
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
