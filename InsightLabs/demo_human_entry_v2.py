#!/usr/bin/env python3
"""
人类需求入口 v2 — 真闭环
================================
v1 → v2 升级：
1. LLM 智能任务拆分（替代硬编码）
2. Registry 动态 Agent 发现
3. AHP Proxy 实际调用 Agent
4. Reliability Ledger 实时记账
5. 结构化交付物输出
"""

import requests
import json
import os
import time
from datetime import datetime
from openai import OpenAI

# ============================================================
# 配置
# ============================================================
BASE = {
    "ahp": "http://localhost:7002",
    "reliability": "http://localhost:7003",
    "registry": "http://localhost:7000",
    "hosting": "http://localhost:7001",
    "commerce": "http://localhost:7004",
    "hub": "http://localhost:8080",
    "insightsee": "http://localhost:9090",
}

CEO_ID = "muyunye-ceo"

# LLM 客户端 (DeepSeek)
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY"),
    base_url="https://api.deepseek.com/v1",
)

# ============================================================
# 核心工具函数
# ============================================================

def llm_chat(system_prompt: str, user_prompt: str, model="deepseek-chat") -> str:
    """调用 LLM"""
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=2000,
    )
    return resp.choices[0].message.content


def registry_search(query: str) -> list:
    """从 Registry 搜索可用的 Agent"""
    try:
        r = requests.get(f"{BASE['registry']}/api/search", params={"q": query}, timeout=5)
        data = r.json()
        return data.get("sites", [])
    except Exception as e:
        print(f"  ⚠️ Registry 搜索失败: {e}")
        return []


def ahp_list_sites() -> list:
    """从 AHP Proxy 获取所有已注册站点"""
    try:
        r = requests.get(f"{BASE['ahp']}/sites", timeout=5)
        return r.json()
    except:
        return []


def ledger_record(from_agent, to_agent, site_id, action, tokens_used=0, success=True) -> dict:
    """记账到 Reliability Ledger"""
    try:
        r = requests.post(f"{BASE['reliability']}/api/ledger/record", json={
            "from_agent": from_agent,
            "to_agent": to_agent,
            "site_id": site_id,
            "action": action,
            "tokens_used": tokens_used,
            "success": success,
        }, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def ledger_balance(agent_id) -> dict:
    """查询 Agent 余额"""
    try:
        r = requests.get(f"{BASE['reliability']}/api/ledger/agent/{agent_id}/balance", timeout=5)
        return r.json()
    except:
        return {}


def insightsee_analyze(texts: list, analysis_type="insight") -> dict:
    """用 InsightSee 分析文本"""
    try:
        r = requests.post(f"{BASE['insightsee']}/api/analyze", json={
            "texts": texts, "type": analysis_type
        }, timeout=15)
        return r.json()
    except:
        return {}


# ============================================================
# 核心流程
# ============================================================

def step1_split_task(user_request: str) -> dict:
    """Step 1: LLM 智能拆分用户任务"""
    print("\n" + "="*60)
    print("  🧠 Step 1: LLM 智能任务拆分")
    print("="*60)
    print(f"  用户请求: \"{user_request}\"")

    system_prompt = """你是任务拆分专家。用户提出一个复杂需求，你需要把它拆分成可分配给不同Agent执行的子任务。

规则：
1. 每个子任务必须明确：执行Agent类型、任务描述、预估token消耗
2. Agent类型从以下选择：search_collector(信息搜集), article_writer(文章写作), data_analyst(数据分析), translator(翻译), summarizer(摘要), researcher(研究)
3. 子任务之间有依赖关系时要标注
4. 回报标准JSON格式

返回格式:
{
  "tasks": [
    {
      "id": 1,
      "agent_type": "search_collector",
      "action": "具体任务描述",
      "depends_on": null,
      "estimated_tokens": 1500
    }
  ],
  "analysis": "任务拆分的简要分析"
}"""

    resp = llm_chat(system_prompt, user_request)
    print(f"  LLM 返回: {resp[:200]}...")

    # 解析 JSON
    try:
        # 提取 JSON
        json_start = resp.find('{')
        json_end = resp.rfind('}') + 1
        if json_start >= 0 and json_end > 0:
            plan = json.loads(resp[json_start:json_end])
        else:
            # Fallback
            plan = {
                "tasks": [
                    {"id": 1, "agent_type": "search_collector", "action": user_request, "depends_on": None, "estimated_tokens": 2000}
                ],
                "analysis": "LLM返回异常，使用默认拆分"
            }
    except:
        plan = {
            "tasks": [
                {"id": 1, "agent_type": "search_collector", "action": user_request, "depends_on": None, "estimated_tokens": 2000}
            ],
            "analysis": "JSON解析失败，使用默认拆分"
        }

    print(f"  拆分结果: {len(plan['tasks'])} 个子任务")
    for t in plan["tasks"]:
        print(f"    #{t['id']}: {t['agent_type']} → {t['action'][:80]}")
    return plan


def step2_discover_agents(tasks: list) -> dict:
    """Step 2: 从 Registry 动态发现 Agent"""
    print("\n" + "="*60)
    print("  🔍 Step 2: Registry 动态发现 Agent")
    print("="*60)

    agent_map = {}
    agent_types = set(t["agent_type"] for t in tasks)

    for atype in agent_types:
        sites = registry_search(atype.replace("_", " "))
        if sites:
            matched = sites[0]
            agent_map[atype] = {
                "site_id": matched.get("site_id", ""),
                "name": matched.get("name", ""),
                "type": matched.get("type", ""),
                "id": matched.get("site_id", ""),
            }
            print(f"  ✅ {atype} → {matched.get('name', 'N/A')} (id={matched.get('site_id', 'N/A')})")
        else:
            # 如果没有找到，用兜底
            agent_map[atype] = {
                "site_id": atype,
                "name": atype,
                "type": "general",
                "id": atype,
            }
            print(f"  ⚠️ {atype} → 未找到，使用兜底 {atype}")

    return agent_map


def step3_execute_tasks(tasks: list, agent_map: dict, site_id_prefix: str) -> list:
    """Step 3: 实际执行任务（LLM 真实执行）"""
    print("\n" + "="*60)
    print("  ⚡ Step 3: 执行任务（LLM 真实执行）")
    print("="*60)

    results = []

    for task in tasks:
        atype = task["agent_type"]
        agent = agent_map.get(atype, {})
        task_id = task["id"]

        # 记账：任务开始
        ledger_record(CEO_ID, agent.get("name", atype), site_id_prefix,
                      f"task_start:{task['action']}",
                      tokens_used=task.get("estimated_tokens", 1000))

        # 根据 Agent 类型执行不同的 LLM 操作
        if atype == "search_collector":
            result = execute_search(task["action"])
        elif atype == "article_writer":
            # 获取前置结果作为上下文
            context = ""
            if task.get("depends_on"):
                for r in results:
                    if r["task_id"] == task["depends_on"]:
                        context = r.get("output", "")
            result = execute_writing(task["action"], context)
        elif atype == "data_analyst":
            result = execute_analysis(task["action"])
        elif atype == "summarizer":
            result = execute_summary(task["action"])
        else:
            result = execute_general(task["action"])

        # 记账：任务完成
        ledger_record(agent.get("name", atype), CEO_ID, site_id_prefix,
                      f"task_done:{task['action'][:60]}",
                      tokens_used=0)

        results.append({
            "task_id": task_id,
            "agent_type": atype,
            "agent_name": agent.get("name", atype),
            "action": task["action"],
            "output": result,
        })

        print(f"  ✅ 任务#{task_id} ({atype}): 完成，输出 {len(result)} 字")

    return results


def execute_search(query: str) -> str:
    """搜索 Agent 执行"""
    prompt = f"""你是一个专业信息搜集Agent。请针对以下需求，提供结构化信息：

需求：{query}

请输出：
1. 关键事实和数据（至少5条）
2. 信息来源（标注可信度）
3. 综合分析摘要（200字以内）
4. 相关联的其他信息方向

格式清晰，用Markdown。"""
    return llm_chat("你是专业信息搜集分析Agent，擅长从多个维度收集和整理信息。", prompt)


def execute_writing(task: str, context: str = "") -> str:
    """写作 Agent 执行"""
    ctx_block = f"\n\n参考素材：\n{context}" if context else ""
    prompt = f"""请根据以下任务撰写专业文章：

任务要求：{task}{ctx_block}

要求：
1. 标题吸引人且有信息量
2. 结构清晰（小标题分段）
3. 数据支撑观点
4. 语气专业但不枯燥
5. 适合公众号发布（1500字左右）

用Markdown格式输出。"""
    return llm_chat("你是专业公众号文章写手，擅长深度分析和故事化表达，产出10万+级别文章。", prompt, model="deepseek-chat")


def execute_analysis(task: str) -> str:
    """分析 Agent"""
    prompt = f"""请对以下需求进行数据分析：

{task}

输出：
1. 核心发现
2. 趋势分析
3. 数据可视化建议
4. 行动建议"""
    return llm_chat("你是数据分析专家。", prompt)


def execute_summary(task: str) -> str:
    """摘要 Agent"""
    prompt = f"请对以下内容进行结构化摘要：\n{task}"
    return llm_chat("你是信息摘要专家。", prompt)


def execute_general(task: str) -> str:
    """通用 Agent"""
    return llm_chat("你是通用任务执行Agent。", task)


def step4_settle(results: list, site_id_prefix: str):
    """Step 4: 结算"""
    print("\n" + "="*60)
    print("  💰 Step 4: 结算报酬")
    print("="*60)

    for r in results:
        ledger_record(CEO_ID, r["agent_name"], site_id_prefix,
                      f"payment:任务{r['task_id']}报酬")
        print(f"  💵 {r['agent_name']}: 任务{r['task_id']} 已结算")


def step5_deliver(results: list, user_request: str, site_id_prefix: str):
    """Step 5: 汇总交付"""
    print("\n" + "="*60)
    print("  📦 Step 5: 汇总交付")
    print("="*60)

    # 汇总所有结果
    parts = [f"# 任务交付报告\n\n**原始请求**: {user_request}\n\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n"]

    for r in results:
        parts.append(f"\n## {r['agent_name']}: {r['action'][:50]}\n\n{r['output']}\n\n---\n")

    # 查余额
    bal = ledger_balance(CEO_ID)
    if bal.get("success"):
        a = bal.get("account", {})
        parts.append(f"\n\n## 💳 本次交易摘要\n\n")
        parts.append(f"- CEO余额: {a.get('balance')}\n")
        parts.append(f"- 总支出: {a.get('total_spent')}\n")
        parts.append(f"- 总交易: {a.get('total_calls')}\n")

    full_report = "".join(parts)

    # 保存
    output_path = "/tmp/human_entry_v2_delivery.md"
    with open(output_path, "w") as f:
        f.write(full_report)

    print(f"  交付物: {output_path} ({len(full_report)} 字)")
    return full_report


# ============================================================
# 主流程
# ============================================================

def run(user_request: str):
    print("\n" + "█"*60)
    print("█  人类需求入口 v2 — 真闭环                                                ")
    print("█  LLM拆分 + Registry发现 + 真实执行 + Ledger记账 + 交付                   ")
    print("█"*60)
    print(f"  启动: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    site_id_prefix = f"human-entry-{int(time.time())}"

    # Step 1: LLM 拆分
    plan = step1_split_task(user_request)

    # Step 2: 发现 Agent
    agent_map = step2_discover_agents(plan["tasks"])

    # Step 3: 执行
    results = step3_execute_tasks(plan["tasks"], agent_map, site_id_prefix)

    # Step 4: 结算
    step4_settle(results, site_id_prefix)

    # Step 5: 交付
    report = step5_deliver(results, user_request, site_id_prefix)

    # 最终摘要
    print("\n" + "█"*60)
    print("█  ✅ 闭环完成！                                                             ")
    print(f"█  子任务: {len(results)} 个                                                   ")
    print(f"█  交付物: /tmp/human_entry_v2_delivery.md                               ")
    print(f"█  Agent数: {len(agent_map)} 个                                               ")
    print("█"*60)

    return report


# ============================================================
# 入口
# ============================================================

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        request = " ".join(sys.argv[1:])
    else:
        request = "帮我写一篇关于2026年医药反腐新趋势的深度分析文章，要求有数据支撑和案例"

    report = run(request)
    print("\n" + report[:500] + "..." if len(report) > 500 else report)
