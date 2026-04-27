#!/usr/bin/env python3
"""
人类需求入口 MVP — 闭环 Demo
================================
模拟：人对牧云野说一句话 → 拆分 → 调多 Agent → 记账 → 交付

流程：
1. 用户输入任务（例如 "帮我写一篇医药反腐专栏文章"）
2. 牧云野拆分任务
3. 调 search-collector Agent 搜素材
4. 调 article-writer Agent 写文章
5. 记账到 Reliability Ledger
6. 汇总交付
"""

import requests
import json
import time
import subprocess
from datetime import datetime

BASE = {
    "ahp": "http://localhost:7002",
    "reliability": "http://localhost:7003",
    "registry": "http://localhost:7000",
    "hosting": "http://localhost:7001",
    "commerce": "http://localhost:7004",
    "hub": "http://localhost:8080",
    "insightsee": "http://localhost:9090",
}

COLLECTOR = "http://localhost:7004"
AHM_PROXY = "http://localhost:7002"
LEDGER = "http://localhost:7003"


def ledger_record(from_agent, to_agent, site_id, action, tokens_used=0, success=True):
    """记账到 Reliability Ledger"""
    r = requests.post(f"{LEDGER}/api/ledger/record", json={
        "from_agent": from_agent,
        "to_agent": to_agent,
        "site_id": site_id,
        "action": action,
        "tokens_used": tokens_used,
        "success": success,
    }, timeout=10)
    return r.json()


def ledger_balance(agent_id):
    r = requests.get(f"{LEDGER}/api/ledger/agent/{agent_id}/balance", timeout=10)
    return r.json()


def print_divider(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def main():
    print_divider("🧠 人类需求入口 MVP — 闭环 Demo")
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # ========== Step 1: 接收用户任务 ==========
    user_request = "帮我写一篇医药反腐最新动态的深度分析文章"
    print(f"👤 用户请求: \"{user_request}\"")
    print()

    # ========== Step 2: 牧云野自动拆分任务 ==========
    print_divider("🔀 牧云野 任务拆分")
    tasks = [
        {"agent": "search-collector", "action": "搜索医药反腐最新动态，搜集至少5条近期新闻和政策变化", "tokens": 2000},
        {"agent": "article-writer", "action": "基于搜到的素材，写一篇1500字深度分析文章，要求：1)数据支撑 2)案例丰富 3)观点犀利", "tokens": 3500},
    ]
    for i, t in enumerate(tasks):
        print(f"  子任务{i+1}: → {t['agent']} | {t['action'][:50]}...")
    
    site_id = "human-entry-mvp"

    # ========== Step 3: 向 search-collector 下任务单 ==========
    print_divider("📡 分发 → search-collector")
    r1 = ledger_record(
        from_agent="muyunye-ceo",
        to_agent="search-collector",
        site_id=site_id,
        action=f"task:{tasks[0]['action']}",
        tokens_used=tasks[0]['tokens'],
    )
    print(f"  记账结果: {json.dumps(r1, ensure_ascii=False, indent=2)}")

    # ========== Step 4: search-collector 模拟执行 ==========
    print_divider("🔍 search-collector 执行任务")
    search_results = {
        "素材": [
            "2026年4月，国家卫健委发布《关于进一步加强医药购销领域反腐工作的通知》",
            "广东一三甲医院院长因收受回扣被调查，涉案金额超3000万",
            "国务院办公厅印发《2026年纠正医药购销领域和医疗服务中不正之风工作要点》",
            "医药反腐风暴持续：上半年已有87名医院管理层被查",
            "AI辅助审计在医药反腐中的应用：检出异常药品采购模式",
        ],
        "分析摘要": "反腐力度持续加码，从个案查处转向系统性治理，AI技术成为新手段"
    }
    print(f"  搜集到 {len(search_results['素材'])} 条素材")
    print(f"  分析摘要: {search_results['分析摘要']}")
    
    # search-collector 交付
    r2 = ledger_record(
        from_agent="search-collector",
        to_agent="muyunye-ceo",
        site_id=site_id,
        action=f"deliver:5条医药反腐新闻+分析摘要",
        tokens_used=0,
    )
    print(f"  交付记账: ✅")

    # ========== Step 5: 向 article-writer 下任务单 ==========
    print_divider("✍️ 分发 → article-writer")
    r3 = ledger_record(
        from_agent="muyunye-ceo",
        to_agent="article-writer",
        site_id=site_id,
        action=f"task:{tasks[1]['action']}",
        tokens_used=tasks[1]['tokens'],
    )
    print(f"  记账结果: ✅ 计入 {tasks[1]['tokens']} tokens")

    # ========== Step 6: article-writer 模拟执行 ==========
    print_divider("📝 article-writer 执行任务")
    
    # 模拟文章生成（实际应用中这里调 LLM）
    article_text = f"""# 医药反腐新阶段：从个案查处到系统性治理

## 一、风暴持续：数据说话

2026年上半年，全国已有**87名**医院管理层被调查，较2025年同期增长42%。其中三甲医院占比超过60%，涉案金额最高超过3000万元。

## 二、政策升级：从治标到治本

国务院办公厅4月印发的《2026年纠正医药购销领域和医疗服务中不正之风工作要点》明确提出三大转变：
1. 从"查个案"转向"建机制"
2. 从"事后追责"转向"事前预防"
3. 从"单一部门"转向"多部门联动"

## 三、技术破局：AI成为反腐新利器

AI辅助审计系统已在部分省份试点，通过分析药品采购数据异常模式，成功发现多起隐蔽的回扣案。技术手段正在成为反腐工作的"第三只眼"。

## 四、深远影响

医药反腐不仅净化了行业风气，更直接降低了药品价格——据测算，反腐风暴已为医保基金节省超过**200亿元**。

---

*本文基于国家卫健委、国务院办公厅公开信息分析撰写*
字数：约1500字
"""
    
    print(f"  文章生成完成: {len(article_text)} 字")
    print(f"  标题: {article_text.split(chr(10))[0]}")
    
    # article-writer 交付
    r4 = ledger_record(
        from_agent="article-writer",
        to_agent="muyunye-ceo",
        site_id=site_id,
        action="deliver:医药反腐深度分析文章.md",
        tokens_used=0,
    )
    print(f"  交付记账: ✅")

    # ========== Step 7: 支付报酬 ==========
    print_divider("💰 结算报酬")
    ledger_record("muyunye-ceo", "search-collector", site_id, "payment:素材搜集费(0.05 USD)")
    ledger_record("muyunye-ceo", "article-writer", site_id, "payment:文章撰写费(0.20 USD)")
    print(f"  search-collector → 0.05 USD")
    print(f"  article-writer → 0.20 USD")

    # ========== Step 8: 汇总交付 ==========
    print_divider("📦 汇总交付给用户")
    
    # 查所有 Agent 余额
    for agent in ["muyunye-ceo", "search-collector", "article-writer"]:
        bal = ledger_balance(agent)
        if bal.get("success"):
            a = bal.get("account", {})
            print(f"  {agent}: 余额={a.get('balance')}, 支出={a.get('total_spent')}, 收入={a.get('total_earned')}")
    
    print(f"\n{'='*60}")
    print(f"  ✅ 闭环完成！")
    print(f"  总耗时: ~3 秒 (模拟)")
    print(f"  交易记录: 7 笔")
    print(f"  交付物: 医药反腐深度分析文章 (约1500字)")
    print(f"{'='*60}")

    # ========== Step 9: 输出交付物 ==========
    print_divider("📄 最终交付物")
    print(article_text)

    # ========== Step 10: 保存文件 ==========
    output_path = "/tmp/human_entry_mvp_output.md"
    with open(output_path, "w") as f:
        f.write(article_text)
    print(f"\n交付物已保存至: {output_path}")


if __name__ == "__main__":
    main()
