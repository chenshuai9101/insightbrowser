"""InsightBrowser AHP - Core Engine

Routes incoming AHP calls to the appropriate backend engine:
- InsightSee → user feedback analysis
- InsightLens → web page extraction
- Other types → descriptive response
"""
import json
import logging
from typing import Any, AsyncGenerator, Optional

logger = logging.getLogger("ahp.engine")


# ─── Configuration ───────────────────────────────────────────────────

HOSTING_API_BASE = "http://localhost:7001"
REGISTRY_API_BASE = "http://localhost:7000"


# ─── Hosting Site Sync ────────────────────────────────────────────────

class HostingClient:
    """Client for fetching site data from InsightBrowser Hosting."""

    def __init__(self, base_url: str = HOSTING_API_BASE):
        self.base_url = base_url
        self._cache: dict[int, dict] = {}
        self._cache_time = 0

    async def fetch_all_sites(self, force: bool = False) -> list[dict]:
        """Fetch all hosted sites from the Hosting API."""
        import time
        now = time.time()

        if not force and self._cache and (now - self._cache_time) < 30:
            return list(self._cache.values())

        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.base_url}/api/sites")
                if resp.status_code == 200:
                    data = resp.json()
                    sites = data.get("sites", [])
                    self._cache = {s["id"]: s for s in sites}
                    self._cache_time = now
                    return sites
                else:
                    logger.warning(f"Hosting API returned {resp.status_code}")
                    return list(self._cache.values())
        except Exception as e:
            logger.error(f"Failed to fetch sites from Hosting: {e}")
            return list(self._cache.values())

    async def fetch_site(self, site_id: int) -> Optional[dict]:
        """Fetch a single site from the Hosting API."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.base_url}/api/site/{site_id}")
                if resp.status_code == 200:
                    site = resp.json()
                    self._cache[site["id"]] = site
                    return site
                else:
                    return self._cache.get(site_id)
        except Exception as e:
            logger.error(f"Failed to fetch site {site_id}: {e}")
            return self._cache.get(site_id)


hosting_client = HostingClient()


# ─── InsightSee Engine (Built-in) ──────────────────────────────────────

class InsightSeeEngine:
    """Built-in InsightSee engine for user feedback analysis.

    Implements the core algorithm described in the InsightSee whitepaper:
    analyze user feedback text → structured insight dimensions.
    """

    # 6 demand dimensions
    DIMENSIONS = [
        "功能需求",     # Feature requests
        "体验问题",     # UX/experience issues
        "性能问题",     # Performance concerns
        "价格敏感",     # Price sensitivity
        "服务需求",     # Service/support needs
        "竞品对比",     # Competitive comparison
    ]

    # Industry keywords (simplified)
    INDUSTRY_KEYWORDS = {
        "电商": ["发货", "退货", "物流", "客服", "退款", "商品"],
        "SaaS": ["功能", "界面", "卡顿", "加载", "集成", "API"],
        "金融": ["利率", "额度", "审批", "风控", "费率", "到账"],
        "教育": ["课程", "老师", "学习", "作业", "考试", "分数"],
        "游戏": ["氪金", "平衡", "卡顿", "外挂", "匹配", "延迟"],
        "医疗": ["挂号", "排队", "诊断", "处方", "医保", "预约"],
        "餐饮": ["口味", "等待", "配送", "包装", "优惠", "菜品"],
        "出行": ["导航", "路线", "拥堵", "停车", "充电", "票价"],
    }

    # Sentiment keywords
    POSITIVE_WORDS = ["很好", "不错", "喜欢", "满意", "方便", "好用", "推荐", "快", "棒"]
    NEGATIVE_WORDS = ["太贵", "慢", "卡顿", "差", "不好", "失望", "垃圾", "问题", "bug"]

    @classmethod
    def detect_industry(cls, texts: list[str]) -> str:
        """Detect the most likely industry from text content."""
        combined = " ".join(texts)
        scores = {}
        for industry, keywords in cls.INDUSTRY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in combined)
            if score > 0:
                scores[industry] = score
        if not scores:
            return "通用"
        return max(scores, key=scores.get)

    @classmethod
    def analyze_sentiment(cls, texts: list[str]) -> dict:
        """Analyze overall sentiment from text content."""
        combined = " ".join(texts)
        pos_count = sum(1 for w in cls.POSITIVE_WORDS if w in combined)
        neg_count = sum(1 for w in cls.NEGATIVE_WORDS if w in combined)
        total = pos_count + neg_count
        if total == 0:
            return {"label": "中性", "score": 0.5, "positive": 0, "negative": 0}
        score = pos_count / total
        if score >= 0.7:
            label = "正面"
        elif score <= 0.3:
            label = "负面"
        else:
            label = "中性"
        return {"label": label, "score": round(score, 2), "positive": pos_count, "negative": neg_count}

    @classmethod
    def extract_demands(cls, texts: list[str]) -> list[dict]:
        """Extract structured demands from feedback texts."""
        combined = " ".join(texts)
        demands = []

        for dim in cls.DIMENSIONS:
            # Simple keyword matching for each dimension
            dim_keywords = {
                "功能需求": ["没有", "需要", "希望", "想要", "缺少", "增加", "添加"],
                "体验问题": ["不好用", "难用", "复杂", "麻烦", "不方便", "看不懂"],
                "性能问题": ["卡", "慢", "闪退", "崩溃", "加载", "超时", "延迟"],
                "价格敏感": ["太贵", "贵", "便宜", "划算", "性价比", "价格", "优惠", "免费"],
                "服务需求": ["客服", "售后", "服务", "退换", "保修", "维修", "支持"],
                "竞品对比": ["比", "不如", "没有", "也", "其他", "人家", "竞品"],
            }

            keywords = dim_keywords.get(dim, [])
            matched = [kw for kw in keywords if kw in combined]

            if matched or dim == "功能需求":  # Always include functional needs
                frequency = sum(1 for kw in matched if kw in combined) if matched else 1
                demands.append({
                    "dimension": dim,
                    "frequency": frequency,
                    "keywords": matched if matched else [],
                    "relevance": round(min(frequency / len(keywords) if keywords else 0.1, 1.0), 2),
                })

        # Sort by frequency descending
        demands.sort(key=lambda d: d["frequency"], reverse=True)
        return demands

    @classmethod
    def analyze(cls, texts: list[str], industry: str = "") -> dict:
        """Full analysis pipeline: industry → sentiment → demands."""
        detected_industry = industry or cls.detect_industry(texts)
        sentiment = cls.analyze_sentiment(texts)
        demands = cls.extract_demands(texts)

        return {
            "industry": detected_industry,
            "sentiment": sentiment,
            "demands": demands,
            "total_texts": len(texts),
            "summary": cls.generate_summary(demands, sentiment),
        }

    @classmethod
    def generate_summary(cls, demands: list[dict], sentiment: dict) -> str:
        """Generate a human-readable summary of the analysis."""
        top_demands = demands[:3]
        demand_str = "、".join([d["dimension"] for d in top_demands]) if top_demands else "无明显需求聚焦"

        sentiment_str = sentiment["label"]
        if sentiment["score"] > 0.7:
            sentiment_str = "偏正面"
        elif sentiment["score"] < 0.3:
            sentiment_str = "偏负面"

        return f"共发现{len(demands)}个需求维度,主要集中在{demand_str},整体情绪{sentiment_str}。"


# ─── InsightLens Engine (Built-in) ─────────────────────────────────────

class InsightLensEngine:
    """Built-in InsightLens engine for web page extraction.

    Extracts content from URLs using simple HTTP fetching.
    """

    @classmethod
    async def extract(cls, url: str, format: str = "markdown") -> dict:
        """Extract content from a URL."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                resp = await client.get(url, headers={
                    "User-Agent": "InsightLens/1.0 (Agent Web Extractor)"
                })

                if resp.status_code != 200:
                    return {
                        "success": False,
                        "error": f"HTTP {resp.status_code}: {resp.reason_phrase}",
                        "url": url,
                    }

                content_type = resp.headers.get("content-type", "")
                html = resp.text

                if format == "raw":
                    return cls._raw_result(url, html, content_type)

                return cls._extract_structured(url, html)

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "url": url,
            }

    @classmethod
    def _raw_result(cls, url: str, html: str, content_type: str) -> dict:
        return {
            "success": True,
            "url": url,
            "content_type": content_type,
            "size": len(html),
            "raw": html[:50000],  # Limit raw output size
            "format": "raw",
        }

    @classmethod
    def _extract_structured(cls, url: str, html: str) -> dict:
        """Extract structured content from HTML."""
        import re

        # Extract title
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.DOTALL | re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else ""

        # Extract meta description
        desc_match = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']', html)
        description = desc_match.group(1).strip() if desc_match else ""

        # Remove scripts, styles, and HTML tags
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        # Extract headings
        headings = []
        for level in range(1, 4):
            pattern = re.compile(rf'<h{level}[^>]*>(.*?)</h{level}>', re.DOTALL | re.IGNORECASE)
            for m in pattern.finditer(html):
                heading_text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
                if heading_text:
                    headings.append({"level": level, "text": heading_text})

        # Extract links
        links = []
        for m in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.DOTALL | re.IGNORECASE):
            href = m.group(1).strip()
            link_text = re.sub(r'<[^>]+>', '', m.group(2)).strip()
            if href and link_text and not href.startswith(('#', 'javascript:')):
                links.append({"href": href, "text": link_text})

        return {
            "success": True,
            "url": url,
            "title": title,
            "description": description,
            "text_length": len(text),
            "text": text[:80000],  # Limit text extraction
            "headings": headings[:30],
            "links": links[:50],
            "format": "structured",
        }


# ─── Generic Engine ────────────────────────────────────────────────────

class GenericEngine:
    """Generic engine for non-specialized sites."""

    @classmethod
    def info(cls, site_name: str, description: str) -> dict:
        return {
            "type": "generic",
            "name": site_name,
            "description": description,
            "note": "This is a generic site. No specialized processing engine available.",
        }


# ─── Main Dispatcher ──────────────────────────────────────────────────

class AHPEngine:
    """Main AHP Engine - routes requests to the appropriate backend."""

    @staticmethod
    async def execute_action(site: dict, action_name: str,
                             action_data: dict) -> dict:
        """Execute an action on a site.

        Routes based on:
        - site.site_type (e.g., "analysis" → InsightSee)
        - action_data.type (e.g., "insight" → InsightSee)
        - action_data.type (e.g., "extract" → InsightLens)
        """
        from models import HostingSite, AHPActionResponse

        site_model = HostingSite(site)
        ahp_type = site_model.ahp_type
        action_type = action_data.get("type", action_name)

        logger.info(
            f"Executing action '{action_name}' (type={action_type}) "
            f"on site '{site_model.name}' (ahp_type={ahp_type})"
        )

        try:
            if ahp_type == "insightsee" or action_type == "insight":
                # Route to InsightSee engine
                texts = action_data.get("texts", action_data.get("data", []))
                if isinstance(texts, str):
                    texts = [texts]
                if not texts:
                    return AHPActionResponse(
                        success=False,
                        error="No text data provided for insight analysis",
                        action=action_name,
                    ).to_dict()

                industry = action_data.get("industry", "")
                result = InsightSeeEngine.analyze(texts, industry)

                return AHPActionResponse(
                    success=True,
                    data=result,
                    action=action_name,
                ).to_dict()

            elif ahp_type == "insightlens" or action_type == "extract":
                # Route to InsightLens engine
                url = action_data.get("url", action_data.get("data", ""))
                if not url:
                    return AHPActionResponse(
                        success=False,
                        error="No URL provided for extraction",
                        action=action_name,
                    ).to_dict()

                fmt = action_data.get("format", "structured")
                result = await InsightLensEngine.extract(url, fmt)

                return AHPActionResponse(
                    success=result.get("success", False),
                    data=result,
                    action=action_name,
                ).to_dict()

            else:
                # Generic site - return descriptive info
                return AHPActionResponse(
                    success=True,
                    data=GenericEngine.info(site_model.name, site_model.description),
                    action=action_name,
                ).to_dict()

        except Exception as e:
            logger.exception(f"Engine error for {action_name}")
            return AHPActionResponse(
                success=False,
                error=str(e),
                action=action_name,
            ).to_dict()

    @staticmethod
    async def stream_action(site: dict, action_name: str,
                            action_data: dict) -> AsyncGenerator[str, None]:
        """Stream action results as SSE events."""
        from models import HostingSite

        site_model = HostingSite(site)
        ahp_type = site_model.ahp_type
        action_type = action_data.get("type", action_name)

        # Send start event
        yield f"data: {json.dumps({'event': 'start', 'action': action_name, 'site': site_model.name})}\n\n"

        try:
            if ahp_type == "insightsee" or action_type == "insight":
                texts = action_data.get("texts", action_data.get("data", []))
                if isinstance(texts, str):
                    texts = [texts]

                if not texts:
                    yield f"data: {json.dumps({'event': 'error', 'message': 'No text data provided'})}\n\n"
                    yield "event: done\ndata: \n\n"
                    return

                # Stream each step
                yield f"data: {json.dumps({'event': 'progress', 'step': 'industry_detection', 'message': 'Detecting industry...'})}\n\n"
                industry = InsightSeeEngine.detect_industry(texts)

                yield f"data: {json.dumps({'event': 'progress', 'step': 'sentiment_analysis', 'message': 'Analyzing sentiment...'})}\n\n"
                sentiment = InsightSeeEngine.analyze_sentiment(texts)

                yield f"data: {json.dumps({'event': 'progress', 'step': 'demand_extraction', 'message': 'Extracting demands...'})}\n\n"
                demands = InsightSeeEngine.extract_demands(texts)

                summary = InsightSeeEngine.generate_summary(demands, sentiment)

                result = {
                    "industry": industry,
                    "sentiment": sentiment,
                    "demands": demands,
                    "total_texts": len(texts),
                    "summary": summary,
                }

                yield f"data: {json.dumps({'event': 'result', 'data': result})}\n\n"

            elif ahp_type == "insightlens" or action_type == "extract":
                url = action_data.get("url", action_data.get("data", ""))
                if not url:
                    yield f"data: {json.dumps({'event': 'error', 'message': 'No URL provided'})}\n\n"
                    yield "event: done\ndata: \n\n"
                    return

                yield f"data: {json.dumps({'event': 'progress', 'step': 'fetching', 'message': f'Fetching {url}...'})}\n\n"
                result = await InsightLensEngine.extract(url)

                yield f"data: {json.dumps({'event': 'result', 'data': result})}\n\n"

            else:
                result = GenericEngine.info(site_model.name, site_model.description)
                yield f"data: {json.dumps({'event': 'result', 'data': result})}\n\n"

        except Exception as e:
            logger.exception(f"Stream error for {action_name}")
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"

        yield "event: done\ndata: \n\n"

    @staticmethod
    async def get_site_data(site: dict, filters: dict) -> dict:
        """Get data from a site (simplified - returns site metadata)."""
        from models import HostingSite, AHPDataResponse
        
        site_model = HostingSite(site)

        data = {
            "site_id": site_model.id,
            "name": site_model.name,
            "type": site_model.site_type,
            "description": site_model.description,
            "capabilities": site_model.capabilities,
            "status": site_model.status,
            "call_count": site_model.call_count,
            "created_at": site_model.created_at,
            "updated_at": site_model.updated_at,
        }

        # Apply simple filters if provided
        if filters:
            filtered = {}
            for key, value in filters.items():
                if key in data and str(data[key]) == str(value):
                    filtered[key] = data[key]
            if filtered:
                data = filtered

        return AHPDataResponse(
            success=True,
            data=data,
            total=1,
        ).to_dict()
