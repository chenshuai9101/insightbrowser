"""Commerce Bridge - URL → Agent JSON Converter

Uses built-in HTTP fetching for web content extraction (replaces
InsightLens dependency to avoid import path issues).
Analyzes extracted text with simple keyword matching (replaces
InsightSee dependency).
"""
import logging
import sys
import re
import os
from typing import Optional

import httpx

logger = logging.getLogger("commerce.converter")


# ─── Try to import real engines (optional) ────────────────────────────

_has_insightlens = False
_has_insightsee = False
_InsightLensEngine = None
_InsightSeeEngine = None

try:
    from services.engine import InsightLensEngine as _InsightLensEngine
    _has_insightlens = True
    logger.info("✅ Imported real InsightLens engine")
except ImportError:
    logger.info("ℹ️ InsightLens engine not available, using built-in HTTP extractor")

try:
    from services.engine import InsightSeeEngine as _InsightSeeEngine
    _has_insightsee = True
    logger.info("✅ Imported real InsightSee engine")
except ImportError:
    logger.info("ℹ️ InsightSee engine not available, using built-in text analyzer")


# ─── Built-in InsightLens (HTTP page extraction) ──────────────────────

async def _builtin_extract(url: str) -> dict:
    """Simple HTTP-based page extraction when InsightLens engine is unavailable."""
    result = {
        "title": "",
        "description": "",
        "text": "",
        "headings": [],
        "links": [],
        "products": [],
    }

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers={
                "User-Agent": "InsightBrowser/1.0 (CommerceBridge; +https://insightbrowser.app)"
            })
            if resp.status_code != 200:
                logger.warning(f"HTTP {resp.status_code} fetching {url}")
                return result

            html = resp.text
            result["text"] = html

            # Extract <title>
            m = re.search(r'<title[^>]*>(.*?)</title>', html, re.DOTALL | re.IGNORECASE)
            if m:
                result["title"] = m.group(1).strip()

            # Extract <meta name="description">
            m = re.search(
                r'<meta\s+[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']',
                html, re.DOTALL | re.IGNORECASE
            )
            if not m:
                m = re.search(
                    r'<meta\s+[^>]*content=["\']([^"\']*)["\'][^>]*name=["\']description["\']',
                    html, re.DOTALL | re.IGNORECASE
                )
            if m:
                result["description"] = m.group(1).strip()[:500]

            # Extract headings
            for tag in ['h1', 'h2', 'h3']:
                for m in re.finditer(
                    rf'<{tag}[^>]*>(.*?)</{tag}>', html, re.DOTALL | re.IGNORECASE
                ):
                    text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
                    if text and len(text) < 200:
                        result["headings"].append(text[:100])

            # Extract links
            seen = set()
            for m in re.finditer(
                r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
                html, re.DOTALL | re.IGNORECASE
            ):
                href = m.group(1).strip()
                text = re.sub(r'<[^>]+>', '', m.group(2)).strip()
                if href and text and href not in seen and len(text) < 200:
                    seen.add(href)
                    result["links"].append({
                        "href": href,
                        "text": text[:100],
                    })

            logger.info(f"Extracted {url}: title='{result['title'][:50]}', "
                        f"{len(result['links'])} links, {len(result['headings'])} headings")

    except Exception as e:
        logger.warning(f"Failed to extract {url}: {e}")

    return result


async def extract_url(url: str) -> dict:
    """Extract content from URL using InsightLens if available, else built-in."""
    if _has_insightlens and _InsightLensEngine:
        try:
            return await _InsightLensEngine.extract(url)
        except Exception as e:
            logger.warning(f"InsightLens engine failed: {e}, falling back to built-in")

    return await _builtin_extract(url)


# ─── Built-in InsightSee (text analysis) ──────────────────────────────

# Industry keywords
INDUSTRY_KEYWORDS = {
    "手机家电": ["手机", "家电", "数码", "电脑", "笔记本", "平板", "耳机", "相机",
                 "小米", "华为", "苹果", "三星", "OPPO", "vivo", "智能"],
    "餐饮美食": ["餐饮", "美食", "餐厅", "外卖", "火锅", "烧烤", "蛋糕", "咖啡",
                 "奶茶", "快餐", "料理", "小吃"],
    "教育培训": ["教育", "培训", "课程", "学习", "学院", "大学", "辅导", "编程",
                 "英语", "音乐", "美术", "网课"],
    "金融服务": ["金融", "保险", "理财", "投资", "基金", "股票", "银行", "贷款",
                 "信用卡", "支付", "财务"],
    "服装时尚": ["服装", "服饰", "时尚", "鞋子", "包包", "配饰", "女装", "男装",
                 "潮牌", "运动", "内衣"],
    "美妆个护": ["美妆", "护肤", "化妆品", "香水", "面膜", "口红", "护发",
                 "美容", "医美"],
    "家居生活": ["家居", "家具", "家装", "床上用品", "厨具", "灯具", "收纳",
                 "装饰", "日用品"],
    "母婴亲子": ["母婴", "宝宝", "奶粉", "童装", "玩具", "婴儿车", "孕妇"],
    "运动户外": ["运动", "健身", "户外", "跑步", "瑜伽", "骑行", "露营",
                 "登山", "游泳"],
    "其他": [],
}

# Analysis dimensions
DIMENSION_KEYWORDS = {
    "质量": ["质量", "品质", "做工", "材质", "耐用", "牢固", "结实", "质感"],
    "价格": ["价格", "性价比", "实惠", "划算", "贵", "便宜", "价位", "折扣", "优惠"],
    "服务": ["服务", "客服", "售后", "态度", "物流", "快递", "发货", "退换"],
    "体验": ["体验", "感受", "效果", "实用", "好用", "方便", "操作", "简单"],
    "外观": ["外观", "颜值", "设计", "颜色", "款式", "造型", "风格", "好看"],
    "性能": ["性能", "速度", "配置", "功能", "稳定", "流畅", "强大", "能力"],
}


def _builtin_analyze(texts: list[str]) -> dict:
    """Simple keyword-based text analysis when InsightSee is unavailable."""
    combined = " ".join(texts)

    # Determine industry
    industry_scores = {}
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score > 0:
            industry_scores[industry] = score

    if not industry_scores:
        industry = "其他"
    else:
        industry = max(industry_scores, key=industry_scores.get)

    # Determine demands/keywords by dimension
    demands = []
    for dimension, keywords in DIMENSION_KEYWORDS.items():
        matched = [kw for kw in keywords if kw in combined]
        if matched:
            demands.append({
                "dimension": dimension,
                "keywords": matched[:5],
                "count": len(matched),
            })

    # Simple sentiment analysis
    positive_words = ["好", "棒", "推荐", "赞", "喜欢", "满意", "不错", "值得",
                      "实用", "方便", "强大", "流畅", "稳定", "实惠", "超值"]
    negative_words = ["差", "烂", "贵", "慢", "卡", "问题", "缺陷", "后悔",
                      "失望", "不好", "不行", "没用", "垃圾", "骗人"]

    pos_count = sum(1 for w in positive_words if w in combined)
    neg_count = sum(1 for w in negative_words if w in combined)
    total = pos_count + neg_count
    score = pos_count / total if total > 0 else 0.5

    if score >= 0.7:
        label = "正面"
    elif score <= 0.3:
        label = "负面"
    else:
        label = "中性"

    sentiment = {
        "label": label,
        "score": round(score, 2),
        "positive_count": pos_count,
        "negative_count": neg_count,
    }

    summary = f"分析{total if total > 0 else 0}个情感标记"
    if industry != "其他":
        summary += f"，主要行业：{industry}"
    if demands:
        summary += f"，涉及{len(demands)}个维度"
    summary += f"，整体{label}（得分{score:.1%}）"

    return {
        "industry": industry,
        "demands": demands,
        "sentiment": sentiment,
        "summary": summary,
        "engine": "builtin",
    }


def analyze_texts(texts: list[str]) -> dict:
    """Analyze texts using InsightSee if available, else built-in analysis."""
    if _has_insightsee and _InsightSeeEngine:
        try:
            result = _InsightSeeEngine.analyze(texts)
            result["engine"] = "InsightSee"
            return result
        except Exception as e:
            logger.warning(f"InsightSee engine failed: {e}, falling back to built-in")

    return _builtin_analyze(texts)


# ─── Product Detection ─────────────────────────────────────────────────

PRODUCT_URL_PATTERNS = [
    r'/product/', r'/products/', r'/item/', r'/items/',
    r'/goods/', r'/p/\d+', r'/shop/', r'/detail/',
    r'/spu/', r'/sku/', r'/show/',
]

PRODUCT_KEYWORDS = [
    '购买', '详情', '查看', '选购', '商品', '产品',
    '型号', '系列', '规格', '报价', '价格',
    '加入购物车', '立即购买',
]


def detect_products_from_links(links: list[dict]) -> list[dict]:
    """Detect product links from extracted page links."""
    products = []
    seen_urls = set()

    for link in links:
        href = link.get("href", "")
        text = link.get("text", "")

        if not href or href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
            continue

        url_lower = href.lower()
        if url_lower in seen_urls:
            continue

        is_product = any(
            re.search(pat, url_lower) for pat in PRODUCT_URL_PATTERNS
        ) or any(kw in text for kw in PRODUCT_KEYWORDS)

        if is_product and text:
            seen_urls.add(url_lower)
            products.append({
                "name": text.strip()[:80],
                "url": href,
            })

    return products


def get_price_info(text: str) -> list[str]:
    """Extract price information from text."""
    prices = []
    for pat in [r'¥\s*[\d,]+\.?\d*', r'￥\s*[\d,]+\.?\d*',
                r'\$\s*[\d,]+\.?\d*', r'€\s*[\d,]+\.?\d*']:
        prices.extend(re.findall(pat, text))
    return prices[:20]


CATEGORY_MAP = {
    "手机": "手机家电",
    "家电": "手机家电",
    "数码": "手机家电",
    "电脑": "手机家电",
    "餐饮": "餐饮美食",
    "美食": "餐饮美食",
    "外卖": "餐饮美食",
    "教育": "教育培训",
    "培训": "教育培训",
    "课程": "教育培训",
    "金融": "金融服务",
    "保险": "金融服务",
    "理财": "金融服务",
    "服装": "服装时尚",
    "时尚": "服装时尚",
    "美妆": "美妆个护",
    "护肤": "美妆个护",
    "家居": "家居生活",
    "家具": "家居生活",
    "母婴": "母婴亲子",
    "宝宝": "母婴亲子",
    "运动": "运动户外",
    "健身": "运动户外",
    "其他": "其他",
}


def map_display_category(category: str) -> str:
    return CATEGORY_MAP.get(category, "其他")


# ─── Main Conversion Logic ────────────────────────────────────────────

async def convert_url_to_agent_json(
    url: str,
    name: str,
    category: str,
    description: str,
) -> dict:
    """Core conversion: URL → structured data → agent.json.

    Steps:
        1. Extract content from URL
        2. Analyze text content
        3. Detect products from links
        4. Build agent.json with all discovered information
    """
    # Step 1: Extract content
    content = await extract_url(url)

    logger.info(f"Extracted content from {url}: "
                f"title={content.get('title','')[:50]}, "
                f"links={len(content.get('links',[]))}, "
                f"headings={len(content.get('headings',[]))}")

    # Step 2: Analyze via InsightSee
    texts_for_analysis = [
        description,
        content.get("title", ""),
        content.get("description", ""),
        content.get("text", "")[:2000],
    ]
    analysis = analyze_texts(texts_for_analysis)

    logger.info(f"Analysis: industry={analysis.get('industry','')}, "
                f"engine={analysis.get('engine','?')}")

    # Step 3: Detect products
    links = content.get("links", [])
    detected_products = detect_products_from_links(links)
    prices = get_price_info(content.get("text", ""))

    # Step 4: Generate capability descriptions
    browse_desc = f"浏览{name}的商品列表"
    if detected_products:
        product_names = [p["name"] for p in detected_products[:6]]
        browse_desc += f"，包括：{'、'.join(product_names)}"

    # Step 5: Build complete agent.json
    agent_json = {
        "ahp_version": "0.1",
        "agent": {
            "name": name,
            "type": "commerce",
            "category": category,
            "display_category": map_display_category(category),
            "description": description,
            "source_url": url,
        },
        "capabilities": [
            {
                "id": "browse_products",
                "name": "浏览商品",
                "description": browse_desc,
                "parameters": [
                    {"name": "category", "type": "string", "description": "商品分类筛选"}
                ],
            },
            {
                "id": "search_products",
                "name": "搜索商品",
                "description": f"在{name}搜索指定商品",
                "parameters": [
                    {"name": "query", "type": "string", "description": "搜索关键词"}
                ],
            },
        ],
        "pricing": {
            "per_call": 1,
            "free_tier_per_day": 100,
        },
        "content": {
            "title": content.get("title", ""),
            "description": content.get("description", ""),
            "headings": content.get("headings", [])[:20],
            "links_count": len(links),
            "products": detected_products,
            "prices_found": prices,
        },
        "meta": {
            "industry": analysis.get("industry", ""),
            "keywords": analysis.get("demands", []),
            "sentiment": analysis.get("sentiment", {}),
            "analysis_summary": analysis.get("summary", ""),
            "engine": analysis.get("engine", "builtin"),
            "created_by": "commerce-bridge",
        },
    }

    return agent_json
