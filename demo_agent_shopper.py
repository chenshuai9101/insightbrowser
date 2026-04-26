#!/usr/bin/env python3
"""Demo: Agent 采购员 — 模拟 Agent 购物全流程

展示 InsightBrowser 的核心链路：
1. Reliability DB 发现购物类站点
2. Reliability API 获取信任评级
3. 模拟商品数据（含真实 InsightSee 分析逻辑）
4. 综合推荐

运行方式：
    python3 demo_agent_shopper.py
"""
import asyncio
import json
import sys
import os
import sqlite3
from typing import Optional

import httpx


# ═══════════════════════════════════════════════════════════════════════
#  Configuration
# ═══════════════════════════════════════════════════════════════════════

RELIABILITY_URL = "http://localhost:7003"
RELIABILITY_DB = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "reliability.db"
)


# ═══════════════════════════════════════════════════════════════════════
#  Step 1: Discover Commerce Sites from Reliability DB
# ═══════════════════════════════════════════════════════════════════════

async def discover_commerce_sites() -> list[dict]:
    """Step 1: Find commerce-type sites from the Reliability database.

    Reads the Reliability SQLite database directly for registered sites.
    Falls back to simulated data if DB is unavailable.
    """
    print("\n" + "=" * 60)
    print("📡 Step 1: Discovery - Finding Commerce Sites")
    print("=" * 60)

    sites = []

    try:
        conn = sqlite3.connect(RELIABILITY_DB)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT site_id, name, site_type, description, endpoint "
            "FROM sites WHERE site_type = 'commerce' ORDER BY site_id"
        ).fetchall()
        conn.close()

        for row in rows:
            sites.append({
                "site_id": row["site_id"],
                "name": row["name"],
                "type": row["site_type"],
                "description": row["description"],
                "endpoint": row["endpoint"],
                "capabilities": [
                    {"name": "浏览商品", "id": "browse_products"},
                    {"name": "搜索商品", "id": "search_products"},
                ],
            })

        print(f"  Found {len(sites)} commerce sites in Reliability DB:")
        for s in sites:
            print(f"    🏪  {s['name']} (site_id: {s['site_id']})")
    except Exception as e:
        print(f"  ⚠️  Reliability DB error: {e}")

    # Fallback to simulated data if nothing found
    if not sites:
        print(f"  ℹ️  Using fallback simulated data.")
        sites = [
            {
                "site_id": "sim_phone_01",
                "name": "小明手机店",
                "type": "commerce",
                "description": "专注中高端智能手机，代理小米、华为、OPPO 等主流品牌，支持分期付款",
                "capabilities": [
                    {"name": "浏览商品", "id": "browse_products"},
                    {"name": "搜索商品", "id": "search_products"},
                ],
            },
            {
                "site_id": "sim_home_02",
                "name": "智能家居优选",
                "type": "commerce",
                "description": "智能家居一站式采购，智能音箱、智能灯、扫地机器人",
                "capabilities": [
                    {"name": "浏览商品", "id": "browse_products"},
                    {"name": "搜索商品", "id": "search_products"},
                ],
            },
        ]

    return sites


# ═══════════════════════════════════════════════════════════════════════
#  Step 2: Trust Check from Reliability API
# ═══════════════════════════════════════════════════════════════════════

async def check_trust(site_name: str, site_id: str) -> dict:
    """Step 2: Check trust rating from Reliability Registry."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{RELIABILITY_URL}/api/trust/{site_id}")
            if resp.status_code == 200:
                data = resp.json()
                trust_report = data.get("trust_report", {})
                return {
                    "rating": trust_report.get("rating", "C"),
                    "score": trust_report.get("score", 50),
                    "reliability": trust_report.get("up_time", 0) / 100,
                }
    except Exception as e:
        print(f"    ⚠️  Trust API error: {e}")

    # Fallback: try leaderboard
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{RELIABILITY_URL}/api/leaderboard")
            if resp.status_code == 200:
                data = resp.json()
                for entry in data.get("leaderboard", []):
                    if entry.get("site_id") == site_id:
                        return {
                            "rating": entry.get("rating", "C"),
                            "score": entry.get("score", 50),
                            "reliability": entry.get("up_time", 0) / 100,
                        }
    except Exception:
        pass

    # Hardcoded fallback
    trust_scores = {
        "小明手机店": {"rating": "A", "score": 85, "reliability": 0.92},
        "智能家居优选": {"rating": "B", "score": 72, "reliability": 0.78},
    }
    return trust_scores.get(site_name, {"rating": "C", "score": 50, "reliability": 0.5})


# ═══════════════════════════════════════════════════════════════════════
#  Step 3: Simulated Product Data
# ═══════════════════════════════════════════════════════════════════════

def get_products_for_site(site_name: str, category: str = "手机") -> list[dict]:
    """Simulated product catalog for each store."""
    catalog = {
        "小明手机店": [
            {
                "name": "小米14 Pro",
                "price": 4999,
                "category": "手机",
                "url": "https://example.com/phone/xiaomi14pro",
                "review_url": "https://example.com/reviews/xiaomi14pro",
                "rating": 4.8,
                "reviews_count": 1234,
                "review_texts": [
                    "拍照效果非常好，徕卡镜头名不虚传",
                    "系统流畅，MIUI 15 优化很好",
                    "续航不错，一天一充够用",
                    "价格有点贵，但物有所值",
                    "推荐购买，性价比很高",
                ],
            },
            {
                "name": "华为 Mate 60 Pro",
                "price": 6999,
                "category": "手机",
                "url": "https://example.com/phone/mate60pro",
                "review_url": "https://example.com/reviews/mate60pro",
                "rating": 4.9,
                "reviews_count": 2567,
                "review_texts": [
                    "卫星通信功能太强大了",
                    "拍照一流，夜景模式无敌",
                    "鸿蒙系统生态很好用",
                    "价格偏高，但是国产之光",
                    "信号非常好，比苹果强太多",
                ],
            },
            {
                "name": "一加 Ace 3",
                "price": 2999,
                "category": "手机",
                "url": "https://example.com/phone/oneplusace3",
                "review_url": "https://example.com/reviews/oneplusace3",
                "rating": 4.6,
                "reviews_count": 856,
                "review_texts": [
                    "性价比极高，这个价位无敌",
                    "充电速度太快了，100W就是爽",
                    "屏幕很不错，护眼模式好用",
                    "系统干净，没有广告",
                    "这个价格能买到这样的配置，超值",
                ],
            },
            {
                "name": "Redmi K70",
                "price": 2499,
                "category": "手机",
                "url": "https://example.com/phone/redmik70",
                "review_url": "https://example.com/reviews/redmik70",
                "rating": 4.5,
                "reviews_count": 3456,
                "review_texts": [
                    "这个价位最强的手机",
                    "性能很猛，打游戏不卡",
                    "屏幕素质很好，2K屏",
                    "拍照一般，但日常够用",
                    "电池耐用，一天没问题",
                ],
            },
            {
                "name": "iPhone 15",
                "price": 5999,
                "category": "手机",
                "url": "https://example.com/phone/iphone15",
                "review_url": "https://example.com/reviews/iphone15",
                "rating": 4.7,
                "reviews_count": 5678,
                "review_texts": [
                    "iOS系统还是一如既往的流畅",
                    "信号比上一代好一些了",
                    "拍照真实自然",
                    "价格太贵，性价比不高",
                    "生态体验好，全家桶用户必入",
                ],
            },
            {
                "name": "荣耀 100 Pro",
                "price": 3399,
                "category": "手机",
                "url": "https://example.com/phone/honor100pro",
                "review_url": "https://example.com/reviews/honor100pro",
                "rating": 4.6,
                "reviews_count": 1230,
                "review_texts": [
                    "拍照人像模式很强",
                    "屏幕护眼很棒",
                    "系统流畅度不错",
                    "价格中等偏上",
                    "推荐拍照党入手",
                ],
            },
        ],
        "科技大叔手机店": [
            {
                "name": "小米14 Pro",
                "price": 4999,
                "category": "手机",
                "url": "https://example.com/phone/xiaomi14pro",
                "review_url": "https://example.com/reviews/xiaomi14pro",
                "rating": 4.8,
                "reviews_count": 1234,
                "review_texts": [
                    "拍照效果非常好，徕卡镜头名不虚传",
                    "系统流畅，MIUI 15 优化很好",
                    "很不错，推荐购买",
                ],
            },
            {
                "name": "华为 P60",
                "price": 4499,
                "category": "手机",
                "url": "https://example.com/phone/huawei-p60",
                "review_url": "https://example.com/reviews/huawei-p60",
                "rating": 4.7,
                "reviews_count": 890,
                "review_texts": [
                    "拍照很好，尤其是白天",
                    "系统流畅",
                    "电池一般",
                ],
            },
            {
                "name": "Redmi Note 13 Pro",
                "price": 1899,
                "category": "手机",
                "url": "https://example.com/phone/redminote13pro",
                "review_url": "https://example.com/reviews/redminote13pro",
                "rating": 4.4,
                "reviews_count": 2100,
                "review_texts": [
                    "性价比很高",
                    "屏幕不错",
                    "续航很好",
                    "这个价位很推荐",
                    "适合学生党",
                ],
            },
        ],
        "智能家居优选": [
            {
                "name": "小米智能音箱 Pro",
                "price": 399,
                "category": "智能音箱",
                "url": "https://example.com/speaker/pro",
                "review_url": "https://example.com/reviews/speaker",
                "rating": 4.3,
                "reviews_count": 2340,
                "review_texts": [
                    "音质在这个价位很不错",
                    "智能家居控制很方便",
                    "有时候会误唤醒",
                    "性价比高",
                    "推荐购买",
                ],
            },
        ],
    }
    return catalog.get(site_name, [])


# ═══════════════════════════════════════════════════════════════════════
#  Step 4: InsightSee / Built-in Sentiment Analysis
# ═══════════════════════════════════════════════════════════════════════

async def analyze_reviews(product_name: str, review_texts: list[str]) -> dict:
    """Analyze product reviews for sentiment.

    Uses built-in keyword analysis (mirrors InsightSee logic).
    """
    # This mirrors the builtin analysis from converter.py
    positive_words = ["好", "棒", "推荐", "赞", "喜欢", "满意", "不错", "值得",
                      "实用", "方便", "强大", "流畅", "稳定", "实惠", "超值"]
    negative_words = ["差", "烂", "贵", "慢", "卡", "问题", "缺陷", "后悔",
                      "失望", "不好", "不行", "没用", "垃圾", "骗人"]

    combined = " ".join(review_texts)
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

    # Dimension analysis
    dimensions = {
        "质量": ["质量", "品质", "做工", "材质", "耐用", "质感"],
        "价格": ["价格", "性价比", "实惠", "划算", "贵", "便宜", "折扣"],
        "服务": ["服务", "客服", "售后", "物流", "快递"],
        "体验": ["体验", "感受", "效果", "实用", "好用", "方便"],
        "外观": ["外观", "颜值", "设计", "颜色", "款式", "好看"],
        "性能": ["性能", "速度", "配置", "功能", "稳定", "流畅", "强大"],
    }

    demands = []
    for dim_name, keywords in dimensions.items():
        matched = [kw for kw in keywords if kw in combined]
        if matched:
            demands.append({"dimension": dim_name, "keywords": matched[:3]})

    summary = f"分析{total}个情感标记，整体{label}（得分{score:.1%}）"

    return {
        "engine": "builtin keyword analysis",
        "sentiment": {"label": label, "score": round(score, 2)},
        "demands": demands,
        "summary": summary,
    }


# ═══════════════════════════════════════════════════════════════════════
#  The Agent Shopper
# ═══════════════════════════════════════════════════════════════════════

async def agent_shopper(user_request: str, budget: float = 3000):
    """The main Agent Shopper workflow.

    Full agent decision pipeline:
    1. Discover commerce sites from Reliability DB
    2. Check trust ratings
    3. Scan product catalogs
    4. Filter by budget
    5. Analyze reviews
    6. Sort by sentiment score → Recommend Top 3
    """
    print("\n" + "█" * 60)
    print(f"  🛒  Agent 采购员启动")
    print(f"  📝  用户需求: {user_request}")
    print(f"  💰  预算上限: ¥{budget:,.0f}")
    print("█" * 60)

    # ─── Step 1: Discovery ───────────────────────────────────────────
    commerce_sites = await discover_commerce_sites()

    if not commerce_sites:
        print("\n  ❌  No sites available to shop from.")
        return []

    # ─── Step 2: Trust Check ─────────────────────────────────────────
    print("\n" + "-" * 60)
    print("🛡️  Step 2: Trust Verification (Reliability API)")
    print("-" * 60)

    trusted_sites = []
    for site in commerce_sites:
        trust = await check_trust(
            site.get("name", ""),
            site.get("site_id", ""),
        )
        rating = trust.get("rating", "C")
        score = trust.get("score", 0)

        print(f"  🏪  {site.get('name', 'Unnamed')}: "
              f"Rating={rating}, Score={score}")

        # Only accept sites with B rating or above
        if rating in ("S", "A", "B"):
            trusted_sites.append(site)
            print(f"      ✅  Trustworthy! Adding to shopping list.")
        else:
            print(f"      ⛔  Trust too low (rating {rating}). Skipping.")

    if not trusted_sites:
        print("\n  ℹ️  No trusted sites found. Falling back to all sites.")
        trusted_sites = commerce_sites

    # ─── Step 3: Product Scanning ────────────────────────────────────
    print("\n" + "-" * 60)
    print("📦 Step 3: Product Scanning")
    print("-" * 60)

    all_products = []
    for site in trusted_sites:
        site_name = site.get("name", "Unknown Shop")
        products = get_products_for_site(site_name, "手机")
        print(f"  🏪  {site_name}: Found {len(products)} products")
        for p in products:
            print(f"      📱  {p['name']} — ¥{p['price']:,} "
                  f"(⭐ {p['rating']}/{p.get('reviews_count', 0)} reviews)")
        all_products.extend(products)

    # ─── Step 4: Budget Filtering ────────────────────────────────────
    print("\n" + "-" * 60)
    print(f"💰 Step 4: Budget Filter (≤ ¥{budget:,.0f})")
    print("-" * 60)

    filtered = [p for p in all_products if p["price"] <= budget]
    if not filtered:
        print(f"  😅 No products found within ¥{budget:,.0f} budget.")
        print(f"  💡 建议提高预算或选择其他品类")
        return []

    for p in filtered:
        print(f"  ✅  {p['name']} — ¥{p['price']:,} ✓")

    # ─── Step 5: Review Analysis ─────────────────────────────────────
    print("\n" + "-" * 60)
    print("🔬 Step 5: Review Analysis")
    print("-" * 60)

    for product in filtered:
        print(f"\n  📱  Analyzing: {product['name']}...")
        analysis = await analyze_reviews(
            product["name"],
            product.get("review_texts", []),
        )

        product["analysis"] = analysis
        sentiment = analysis.get("sentiment", {})
        score = sentiment.get("score", 0.5)
        label = sentiment.get("label", "中性")

        print(f"      Sentiment: {label} ({score:.1%})")
        print(f"      Engine: {analysis.get('engine', '?')}")
        print(f"      Summary: {analysis.get('summary', '')[:80]}...")

    # ─── Step 6: Sort & Recommend ────────────────────────────────────
    print("\n" + "-" * 60)
    print("🏆 Step 6: Recommendation Engine")
    print("-" * 60)

    # Sort by sentiment score (descending), then by price (ascending for tiebreaks)
    filtered.sort(
        key=lambda p: (
            p["analysis"].get("sentiment", {}).get("score", 0),
            -p["price"],
        ),
        reverse=True,
    )

    top3 = filtered[:3]

    print(f"\n  🎯  TOP {len(top3)} 推荐:")
    print()
    for i, p in enumerate(top3, 1):
        sentiment = p["analysis"].get("sentiment", {})
        score = sentiment.get("score", 0)
        label = sentiment.get("label", "中性")

        print(f"  #{i}  {p['name']}")
        print(f"      价格: ¥{p['price']:,}")
        print(f"      好评率: {label} ({score:.0%})")
        print(f"      评价数: {p.get('reviews_count', 0)}条")
        print(f"      店铺评分: ⭐ {p.get('rating', 0)}")

        # Show analysis summary
        analysis = p.get("analysis", {})
        if analysis.get("demands"):
            print(f"      用户关注点: ", end="")
            for d in analysis["demands"][:3]:
                kw = d.get("keywords", [])
                if kw:
                    print(f"[{d['dimension']}: {'/'.join(kw[:3])}] ", end="")
            print()

        print()

    # ─── Summary ─────────────────────────────────────────────────────
    print("=" * 60)
    print("📋  Agent 采购报告")
    print("=" * 60)
    print(f"  用户原始需求: {user_request}")
    print(f"  扫描站点: {len(trusted_sites)} 家")
    print(f"  扫描商品: {len(all_products)} 款")
    print(f"  预算筛选: {len(filtered)} 款")
    print(f"  最终推荐: {len(top3)} 款")
    print()
    print(f"  💡 最佳推荐: {top3[0]['name']} — ¥{top3[0]['price']:,}")
    print(f"     (好评率 {top3[0]['analysis']['sentiment']['label']}"
          f" {top3[0]['analysis']['sentiment']['score']:.0%})")
    print()

    return top3


# ═══════════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("""
╔════════════════════════════════════════════════════╗
║     🤖  InsightBrowser Agent 采购员 Demo         ║
║                                                    ║
║  展示完整的 Agent 购物链路：                        ║
║   1. Reliability DB 发现站点                       ║
║   2. Trust 检查 (Reliability API)                  ║
║   3. 商品扫描                                     ║
║   4. 预算筛选                                     ║
║   5. 评价分析 (关键词匹配)                         ║
║   6. 智能推荐 Top 3                                ║
║                                                    ║
╚════════════════════════════════════════════════════╝
    """)

    user_request = "帮我找一款 3000 元以内的手机，好评多的"
    budget = 3000

    result = asyncio.run(agent_shopper(user_request, budget))

    if result:
        print("  ✅  Agent 任务完成！推荐结果已输出")
    else:
        print("  ⚠️  没有找到符合条件的商品")


if __name__ == "__main__":
    main()
