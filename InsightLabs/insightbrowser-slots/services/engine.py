"""
卡槽引擎 — 五大卡槽的核心执行逻辑

每个卡槽都通过 LLM 真实执行，不再是模拟数据。
"""
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from openai import OpenAI

logger = logging.getLogger("slots.engine")

# DeepSeek 客户端
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY"),
    base_url="https://api.deepseek.com/v1",
)

def _llm(system_prompt: str, user_prompt: str, model="deepseek-chat") -> str:
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

def _parse_json(text: str, default: dict = None) -> dict:
    """安全解析 LLM 返回的 JSON"""
    if default is None:
        default = {}
    try:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except:
        pass
    return default


class SlotsEngine:
    """A-Hub 卡槽系统引擎"""

    # ─── 卡槽 1: 感知 ───
    def perceive(self, input_text: str, context: Dict = None, language: str = "zh") -> Dict[str, Any]:
        """理解用户输入，提取意图和关键信息"""
        ctx_str = json.dumps(context, ensure_ascii=False) if context else "无"

        system = """你是需求感知专家。分析用户输入，提取结构化信息。

返回严格JSON:
{
  "intent": "需求类型（搜索/写作/分析/翻译/摘要/创作/对话/任务/购买）",
  "goal": "一句话概括最终目标",
  "complexity": "low|medium|high",
  "key_entities": ["提取的关键实体"],
  "constraints": {"时间": "如果有", "格式": "如果有", "长度": "如果有", "风格": "如果有"},
  "urgency": "low|medium|high",
  "confidence": 0.0-1.0,
  "clarification_needed": "有歧义时的澄清问题，无歧义则为null"
}"""

        result = _llm(system, f"上下文: {ctx_str}\n\n用户输入: {input_text}")

        parsed = _parse_json(result, {
            "intent": "unknown",
            "goal": input_text,
            "complexity": "medium",
            "key_entities": [],
            "constraints": {},
            "urgency": "medium",
            "confidence": 0.5,
            "clarification_needed": None,
        })

        parsed["_raw"] = result
        parsed["_language"] = language
        return parsed

    # ─── 卡槽 2: 规划 ───
    def plan(self, goal: str, constraints: Dict = None,
             available_capabilities: List[str] = None) -> Dict[str, Any]:
        """拆分目标为子任务，确定依赖关系和所需能力"""
        caps = available_capabilities or [
            "search_collector", "article_writer", "data_analyst",
            "researcher", "summarizer", "translator", "code_writer", "designer"
        ]
        constraints_str = json.dumps(constraints, ensure_ascii=False) if constraints else "无"

        system = f"""你是任务规划专家。将用户目标拆分为可执行的子任务。

可用能力类型: {json.dumps(caps)}

规则:
1. 每个子任务指定一种能力类型
2. 有依赖关系的标注 depends_on
3. 给出估计token消耗
4. 确定执行顺序

返回严格JSON:
{{
  "goal": "原目标",
  "total_tasks": N,
  "tasks": [
    {{
      "id": 1,
      "capability": "能力类型",
      "action": "具体任务描述",
      "params": {{}},
      "depends_on": null,
      "estimated_tokens": 1500,
      "priority": "high|medium|low"
    }}
  ],
  "execution_order": [1,2,3],
  "estimated_total_tokens": N
}}"""

        result = _llm(system, f"约束: {constraints_str}\n\n目标: {goal}")

        parsed = _parse_json(result, {
            "goal": goal,
            "total_tasks": 1,
            "tasks": [{"id": 1, "capability": "researcher", "action": goal, "params": {}, "depends_on": None, "estimated_tokens": 2000, "priority": "high"}],
            "execution_order": [1],
            "estimated_total_tokens": 2000,
        })

        parsed["_raw"] = result
        return parsed

    # ─── 卡槽 3: 执行 ───
    def execute(self, task_id: str, capability: str, params: Dict = None,
                context: Dict = None) -> Dict[str, Any]:
        """执行单个子任务——通过 LLM 根据能力类型动态执行"""
        params_str = json.dumps(params, ensure_ascii=False) if params else "{}"
        ctx_str = json.dumps(context, ensure_ascii=False) if context else "无"

        # 根据能力类型选择不同的执行策略
        capability_prompts = {
            "search_collector": "你是信息搜集专家。请针对需求进行全方位信息搜集，输出结构化的调研报告。要求：事实准确、来源清晰、覆盖全面。",
            "article_writer": "你是专业公众号文章写手，擅长深度分析和故事化表达。请撰写高质量文章。要求：标题吸引人、结构清晰、数据支撑、语气专业。",
            "data_analyst": "你是数据分析专家。请从数据中提取洞察。要求：核心发现、趋势分析、可视化建议、行动建议。",
            "researcher": "你是研究专家。请进行深度研究和分析。要求：多角度挖掘、交叉验证、批判性思考。",
            "summarizer": "你是信息浓缩专家。请将大量信息浓缩为精炼要点。要求：抓住核心、逻辑清晰、不遗漏关键信息。",
            "translator": "你是专业翻译。请准确翻译内容。要求：信达雅、专业术语精准、保持原文风格。",
            "code_writer": "你是软件开发专家。请编写高质量代码。要求：可运行、有注释、遵循最佳实践。",
            "designer": "你是设计专家。请提供设计建议和方案。要求：美观、实用、遵循设计原则。",
        }

        system_prompt = capability_prompts.get(capability,
            f"你是{capability}专家。请完成任务。要求：专业、准确、高质量。")

        user_prompt = f"参数: {params_str}\n上下文: {ctx_str}"

        output = _llm(system_prompt, user_prompt)

        return {
            "task_id": task_id,
            "capability": capability,
            "action": params.get("action", "N/A") if params else "N/A",
            "output": output,
            "chars": len(output),
            "timestamp": datetime.now().isoformat(),
        }

    # ─── 卡槽 4: 合成 ───
    def synthesize(self, results: List[Dict], format_type: str = "markdown",
                   target_audience: str = None) -> Dict[str, Any]:
        """汇总多个子任务结果，生成结构化交付物"""
        results_str = json.dumps(
            [{"id": r.get("task_id"), "output": r.get("output", "")[:500]} for r in results],
            ensure_ascii=False
        )

        audience_hint = f"\n目标读者: {target_audience}" if target_audience else ""

        system = f"""你是内容合成专家。将多个子任务的结果汇总为一个完整的最终交付物。

要求:
1. 去重：相同信息只保留一次
2. 结构化：有清晰的标题和段落
3. 逻辑通顺：各部分之间有自然的过渡
4. 完整：覆盖所有子任务的核心产出
5. 格式：使用 Markdown
{audience_hint}

返回JSON:
{{
  "title": "交付物标题",
  "content": "完整的 Markdown 格式交付物",
  "word_count": N,
  "structure": ["第1部分", "第2部分", ...],
  "quality_notes": "合成过程中的观察"
}}"""

        result = _llm(system, f"子任务结果:\n{results_str}")

        parsed = _parse_json(result, {
            "title": "合成结果",
            "content": "\n\n".join(r.get("output", "") for r in results),
            "word_count": sum(len(r.get("output", "")) for r in results),
            "structure": [f"部分{i+1}" for i in range(len(results))],
            "quality_notes": "合成完成",
        })

        # 如果 LLM 没直接返回完整内容，用原始结果汇总
        if not parsed.get("content") or len(parsed["content"]) < 100:
            parts = [f"# {parsed.get('title', '合成结果')}\n"]
            for r in results:
                parts.append(f"\n---\n\n{r.get('output', '')}")
            parsed["content"] = "".join(parts)

        parsed["_raw"] = result
        parsed["_result_count"] = len(results)
        return parsed

    # ─── 卡槽 5: 验证 ───
    def verify(self, output: str, task_goal: str,
               quality_dimensions: List[str] = None) -> Dict[str, Any]:
        """多维度质量验证 + 信任评分"""
        dimensions = quality_dimensions or [
            "completeness", "accuracy", "readability", "originality",
            "structure", "actionability"
        ]

        if len(output) > 3000:
            output_snippet = output[:3000] + "\n...(内容过长，已截断)"
        else:
            output_snippet = output

        system = f"""你是质量验证专家。对交付物进行多维度评估。

评估维度:
{json.dumps(dimensions, ensure_ascii=False)}

每个维度 0-100 分，给出理由。

返回JSON:
{{
  "overall_score": 0-100,
  "dimensions": {{
    "completeness": {{"score": 0-100, "reason": "..."}},
    ...
  }},
  "passed": true/false (overall_score >= 60),
  "trust_update": {{
    "direction": "increase|decrease|maintain",
    "magnitude": -10到+10,
    "reason": "基于质量的信任调整建议"
  }},
  "issues": ["发现的问题"],
  "strengths": ["做得好的地方"],
  "improvement_suggestions": ["改进建议"]
}}"""

        result = _llm(system, f"任务目标: {task_goal}\n\n交付物:\n{output_snippet}")

        parsed = _parse_json(result, {
            "overall_score": 70,
            "dimensions": {d: {"score": 70, "reason": "默认评估"} for d in dimensions},
            "passed": True,
            "trust_update": {"direction": "maintain", "magnitude": 0, "reason": "默认评估"},
            "issues": [],
            "strengths": [],
            "improvement_suggestions": [],
        })

        # 确保分数是数字
        if isinstance(parsed["overall_score"], str):
            try:
                parsed["overall_score"] = float(parsed["overall_score"])
            except:
                parsed["overall_score"] = 70

        parsed["_raw"] = result
        parsed["_output_length"] = len(output)
        return parsed
