"""InsightBrowser Registry - Core Registry Service"""
from models import (
    init_db, register_site, get_site,
    search_sites, list_all_sites, get_stats
)


def bootstrap():
    """Initialize the registry database."""
    init_db()


def register(data: dict) -> dict:
    """Register a new agent site."""
    site = register_site(data)
    return {
        "success": True,
        "message": "站点注册成功",
        "site_id": site["site_id"],
        "site": site,
    }


def lookup(site_id: str) -> dict:
    """Look up a site by ID."""
    site = get_site(site_id)
    if not site:
        return {"success": False, "message": "站点未找到"}
    return {"success": True, "site": site}


def search(q: str = "", type_filter: str = "",
           capability: str = "", page: int = 1,
           page_size: int = 20) -> dict:
    """Search for sites."""
    if not q and not type_filter and not capability:
        result = list_all_sites(page=page, page_size=page_size)
    else:
        result = search_sites(query=q, type_filter=type_filter,
                              capability=capability, page=page,
                              page_size=page_size)
    return {
        "success": True,
        **result,
    }


def stats() -> dict:
    """Get platform statistics."""
    return {"success": True, "stats": get_stats()}
