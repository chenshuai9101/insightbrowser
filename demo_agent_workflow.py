#!/usr/bin/env python3
"""InsightBrowser — 端到端 Agent 工作流演示

展示一个 Agent 如何：
1. 通过 SDK 在 Registry 搜索"用户需求洞察"
2. 发现 InsightSee 站点
3. 通过 AHP 调用它的 analyze 能力
4. 打印结构化结果

前置条件：
1. Registry 运行在 localhost:7000
2. Hosting 运行在 localhost:7001（包含 InsightSee 站点）
3. AHP Proxy 运行在 localhost:7002

运行：
    python3 demo_agent_workflow.py
"""
import sys
import os

# Add SDK to path
SDK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "insightbrowser_sdk")
if SDK_PATH not in sys.path:
    sys.path.insert(0, SDK_PATH)

from insightbrowser_sdk import InsightBrowser, InsightBrowserError


def print_separator(title: str, char: str = "="):
    """Print a formatted section separator."""
    print(f"\n{char * 60}")
    print(f"  {title}")
    print(f"{char * 60}")


def main():
    print("""
╔══════════════════════════════════════════════════╗
║     InsightBrowser Agent Workflow Demo          ║
║     端到端 Agent 工作流演示                     ║
╚══════════════════════════════════════════════════╝
    """)

    # ── Step 0: Initialize SDK ───────────────────────────────────────
    print_separator("Step 0: 初始化 SDK")

    ib = InsightBrowser(
        registry_url="http://localhost:7000",
        ahp_proxy_url="http://localhost:7002",
    )
    print(f"  ✅ SDK 已初始化")
    print(f"  📡 Registry: {ib.registry_url}")
    print(f"  🌐 AHP Proxy: {ib.ahp_proxy_url}")

    # ── Step 1: AHP 代理站点列表 ──────────────────────────────────
    print_separator("Step 1: 获取 AHP 代理的站点列表")

    try:
        proxied_sites = ib.list_proxied_sites()
        print(f"  ✅ 找到 {len(proxied_sites)} 个 AHP 代理站点:")
        for s in proxied_sites:
            print(f"     📍 [{s.site_id}] {s.name} ({s.site_type})")
            print(f"        {s.description[:60]}...")
    except InsightBrowserError as e:
        print(f"  ⚠️  AHP 代理查询失败: {e}")
        proxied_sites = []

    # ── Step 2: Registry 搜索 ─────────────────────────────────────
    print_separator("Step 2: 在 Registry 搜索 '用户需求洞察'")

    try:
        sites = ib.search("用户需求洞察")
        print(f"  ✅ Registry 搜索到 {len(sites)} 个站点:")
        for s in sites:
            caps = ", ".join(s.capability_names[:3])
            print(f"     🔍 [{s.site_id}] {s.name}")
            print(f"        类型: {s.site_type}")
            print(f"        能力: {caps}")
            print(f"        信任等级: {s.trust_level}")
    except InsightBrowserError as e:
        print(f"  ⚠️  Registry 搜索失败: {e}")
        sites = []

    # ── Step 3: 发现最佳站点 ───────────────────────────────────────
    print_separator("Step 3: 发现 InsightSee 站点")

    try:
        site = ib.discover("用户需求洞察")
        if site:
            print(f"  ✅ 发现最佳匹配站点:")
            print(f"     📍 ID: {site.site_id}")
            print(f"     📛 名称: {site.name}")
            print(f"     🏷️  类型: {site.site_type}")
            print(f"     📝 描述: {site.description}")
            print(f"     🎯 能力: {', '.join(site.capability_names)}")
            print(f"     🔗 AHP 端点: {site.ahp_endpoints}")
        else:
            print(f"  ❌ 未发现匹配站点")
            # Fallback: use first proxied site
            if proxied_sites:
                site = proxied_sites[0]
                print(f"  ↪️  回退: 使用第一个代理站点 '{site.name}'")
            else:
                print(f"  ⛔ 无可用站点，无法继续")
                return
    except InsightBrowserError as e:
        print(f"  ❌ 发现失败: {e}")
        return

    # ── Step 4: 获取 agent.json ─────────────────────────────────────
    print_separator("Step 4: 获取 agent.json")

    try:
        agent = ib.agent_json(site)
        print(f"  ✅ agent.json 获取成功:")
        print(f"     协议: {agent.get('protocol', 'N/A')}")
        print(f"     名称: {agent.get('name', 'N/A')}")
        print(f"     类型: {agent.get('type', 'N/A')}")
        print(f"     能力数: {len(agent.get('capabilities', []))}")
    except InsightBrowserError as e:
        print(f"  ⚠️  agent.json 获取失败: {e}")

    # ── Step 5: 获取站点信息 ────────────────────────────────────────
    print_separator("Step 5: 获取站点 Info")

    try:
        info = ib.info(site)
        print(f"  ✅ 站点信息获取成功:")
        print(f"     名称: {info.get('name', info.get('site', {}).get('name', 'N/A'))}")
        if 'capabilities' in info:
            for cap in info['capabilities']:
                print(f"     📋 能力: {cap.get('name', cap.get('id', '?'))}")
                print(f"        描述: {cap.get('description', '')}")
    except InsightBrowserError as e:
        print(f"  ⚠️  站点信息获取失败: {e}")

    # ── Step 6: 调用 AHP Action ─────────────────────────────────────
    print_separator("Step 6: 通过 AHP 调用 analyze 能力")

    # Sample user feedback texts
    sample_texts = [
        "这个产品的功能很好用，但是价格有点贵",
        "发货速度太慢了，等了5天才到",
        "客服态度不错，但是退货流程太复杂",
        "希望能增加离线模式，有时候没网就用不了",
        "比其他家好用，就是界面不够美观",
    ]

    print(f"  📝 输入文本 ({len(sample_texts)} 条反馈):")
    for t in sample_texts:
        print(f"     - \"{t}\"")

    try:
        result = ib.call(site, {
            "action": "analyze",
            "data": {
                "type": "insight",
                "texts": sample_texts,
                "industry": "电商",
            },
        })

        print()
        if result.success:
            print(f"  ✅ AHP 调用成功!")
            data = result.data
            if data:
                # Industry
                print(f"\n  🏭 检测行业: {data.get('industry', '通用')}")

                # Sentiment
                sentiment = data.get('sentiment', {})
                print(f"  💬 情绪分析: {sentiment.get('label', 'N/A')} "
                      f"(得分: {sentiment.get('score', 0):.2f})")
                print(f"     正面词汇: {sentiment.get('positive', 0)}")
                print(f"     负面词汇: {sentiment.get('negative', 0)}")

                # Demands
                print(f"\n  📊 需求维度分析 ({len(data.get('demands', []))} 个):")
                for d in data.get('demands', []):
                    bar = "█" * int(d.get('relevance', 0) * 20)
                    print(f"     [{bar:<20}] {d['dimension']} "
                          f"(相关度: {d.get('relevance', 0):.2f}, "
                          f"频次: {d.get('frequency', 0)})")

                # Summary
                print(f"\n  📋 总结: {data.get('summary', 'N/A')}")
        else:
            print(f"  ❌ AHP 调用失败: {result.error}")
    except InsightBrowserError as e:
        print(f"  ❌ 调用异常: {e}")

    # ── Step 7: 流式调用 (可选) ─────────────────────────────────────
    print_separator("Step 7: SSE 流式调用 (Stream)")

    try:
        events = ib.stream(site, {
            "action": "analyze",
            "data": {
                "type": "insight",
                "texts": sample_texts[:2],  # Fewer texts for stream
            },
        })
        print(f"  ✅ SSE 流式调用成功 ({len(events)} 个事件):")
        for event in events:
            evt_type = event.get("event", "unknown")
            if evt_type == "progress":
                print(f"     ▶️  进度: {event.get('message', '')}")
            elif evt_type == "result":
                print(f"     ✅ 结果: {event.get('data', {}).get('summary', 'N/A')}")
            elif evt_type == "error":
                print(f"     ❌ 错误: {event.get('message', '')}")
            else:
                print(f"     📦 事件: {evt_type}")
    except Exception as e:
        print(f"  ⚠️  SSE 流式调用: {e}")

    # ── Summary ──────────────────────────────────────────────────────
    print_separator("✅ 端到端工作流完成")
    print("""
  Agent 工作流演示已完成:

  1. 🔍 Registry 搜索      →  发现站点
  2. 📍 站点发现           →  最佳匹配
  3. 📄 agent.json         →  协议元数据
  4. ℹ️  站点 Info         →  能力描述
  5. 🚀 AHP Action 调用    →  执行能力
  6. 🌊 SSE Stream         →  流式响应

  Agent 可以通过 SDK 无缝发现和调用
  其他 Agent 的能力，构建真正的
  Agent 原生互联网生态系统。
    """)


if __name__ == "__main__":
    main()
