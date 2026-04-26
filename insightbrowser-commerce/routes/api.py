"""Commerce Bridge - API Routes

POST /convert  - Convert a merchant URL to an agent.json and publish
GET  /sites/{id} - View a converted site's details
"""
import json
import logging
import hashlib

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from models import CommerceSiteRequest, CommerceSiteResponse
from services.converter import convert_url_to_agent_json
from services.publisher import publish_commerce_site

logger = logging.getLogger("commerce.api")

router = APIRouter(tags=["API"])

# In-memory store for converted sites (ephemeral, good enough for demo)
_converted_sites: dict[int, dict] = {}
_next_id = 1
# Cache: (url+name hash) -> response, to avoid re-crawling same URL
_convert_cache: dict[str, dict] = {}


@router.post("/convert", response_model=CommerceSiteResponse)
async def convert_commerce_site(req: CommerceSiteRequest):
    """Convert a merchant URL to an agent.json and publish to the system.

    1. Crawls the merchant URL via InsightLens
    2. Analyzes content via InsightSee
    3. Generates a complete agent.json
    4. Registers in Reliability DB for trust tracking
    5. Makes site discoverable through AHP Proxy
    6. Returns the result with discover URLs
    """
    global _next_id

    # Cache check
    cache_key = hashlib.md5(f"{req.url}|{req.name}".encode()).hexdigest()
    if cache_key in _convert_cache:
        logger.info(f"Cache hit for {req.name}")
        return _convert_cache[cache_key]

    logger.info(f"Converting commerce site: name='{req.name}', url='{req.url}', "
                f"category='{req.category}'")

    # Step 1: Convert URL → structured data → agent.json
    agent_json = await convert_url_to_agent_json(
        url=req.url,
        name=req.name,
        category=req.category,
        description=req.description,
    )

    # Step 2: Publish to Reliability + AHP
    publish_result = await publish_commerce_site(
        name=req.name,
        category=req.category,
        url=req.url,
        description=req.description,
        agent_json=agent_json,
    )

    # Step 3: Cache locally
    site_entry = {
        "id": _next_id,
        "name": req.name,
        "url": req.url,
        "category": req.category,
        "description": req.description,
        "agent_json": agent_json,
        "publish_result": publish_result,
    }
    _converted_sites[_next_id] = site_entry
    _next_id += 1

    site_id_str = publish_result.get("site_id", "")

    # Store in cache
    _convert_cache[cache_key] = True

    return CommerceSiteResponse(
        success=publish_result.get("success", False),
        message="商家入驻成功！Agent 已经发现你的店铺" if publish_result.get("success")
                else f"部分注册失败: {publish_result.get('error', 'unknown error')}",
        agent_json=agent_json,
        registry_id=site_id_str,
        hosting_id=_next_id - 1,
        discover_url=publish_result.get("discover_url"),
    )


@router.get("/sites/{site_id}")
async def get_converted_site(site_id: int):
    """Retrieve a converted site's details."""
    site = _converted_sites.get(site_id)
    if not site:
        raise HTTPException(status_code=404, detail=f"Site {site_id} not found")
    return site
