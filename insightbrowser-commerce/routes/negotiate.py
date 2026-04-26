import json, re, hashlib, time
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["negotiate"])

class NegotiateRequest(BaseModel):
    url: str
    context: Optional[str] = "general"  # finance/creative/ecommerce/general

class NegotiateResponse(BaseModel):
    url: str
    negotiated: bool
    capabilities: Dict[str, Any]
    trust_requirements: Dict[str, Any]
    negotiated_at: float

_negotiate_cache: Dict[str, NegotiateResponse] = {}
CACHE_TTL = 300  # 5 分钟

@router.post("/negotiate", response_model=NegotiateResponse)
async def negotiate(req: NegotiateRequest):
    """Dynamic capability handshake — LLM-powered schema inference"""
    cache_key = hashlib.md5((req.url + req.context).encode()).hexdigest()
    cached = _negotiate_cache.get(cache_key)
    if cached and time.time() - cached.negotiated_at < CACHE_TTL:
        return cached

    # URL pattern analysis
    url_lower = req.url.lower()
    capabilities = {
        "type": "unknown",
        "inferrable": False,
        "confidence": 0.0,
        "available_actions": [],
        "data_formats": ["json", "html"],
    }

    # Detect product pages
    product_patterns = ["/product/", "/item/", "/goods/", "/dp/", "/detail/"]
    if any(p in url_lower for p in product_patterns):
        capabilities["type"] = "product"
        capabilities["inferrable"] = True
        capabilities["confidence"] = 0.85
        capabilities["available_actions"] = ["view", "compare", "search"]

    # Detect article pages
    article_patterns = ["/article/", "/post/", "/blog/", "/news/"]
    if any(p in url_lower for p in article_patterns):
        capabilities["type"] = "content"
        capabilities["inferrable"] = True
        capabilities["confidence"] = 0.75
        capabilities["available_actions"] = ["extract", "summarize", "translate"]

    # Detect API / service pages
    if "/api/" in url_lower or "/graphql" in url_lower:
        capabilities["type"] = "api"
        capabilities["inferrable"] = True
        capabilities["confidence"] = 0.9
        capabilities["available_actions"] = ["query", "subscribe"]

    # Context-sensitive trust requirements
    trust_requirements = {
        "min_rating": "C" if req.context == "general" else
                      "A" if req.context == "finance" else
                      "B",
        "min_uptime": 0.7 if req.context == "general" else
                      0.95 if req.context == "finance" else
                      0.85 if req.context == "ecommerce" else
                      0.5,
    }

    resp = NegotiateResponse(
        url=req.url,
        negotiated=True,
        capabilities=capabilities,
        trust_requirements=trust_requirements,
        negotiated_at=time.time()
    )

    _negotiate_cache[cache_key] = resp
    return resp

@router.get("/negotiate/cache/clear")
async def clear_negotiate_cache():
    _negotiate_cache.clear()
    return {"cleared": True, "count": 0}

