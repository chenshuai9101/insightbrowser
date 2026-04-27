"""
内置工具集
"""
import requests
import aiohttp
import os
from typing import Any, Dict
from openai import OpenAI

from services.tool_registry import Tool, get_tool_registry

# LLM 客户端
_llm_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY"),
    base_url="https://api.deepseek.com/v1",
)


# ─── HTTP 请求工具 ───

async def _http_request(params: dict) -> dict:
    """执行 HTTP 请求"""
    url = params.get("url", "")
    method = params.get("method", "GET").upper()
    headers = params.get("headers", {})
    body = params.get("body", None)
    timeout = params.get("timeout", 30)

    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, headers=headers, json=body, timeout=timeout) as resp:
            text = await resp.text()
            return {
                "status": resp.status,
                "headers": dict(resp.headers),
                "body": text[:10000],  # 限制长度
            }


http_tool = Tool(
    name="http_request",
    description="执行 HTTP 请求调用外部 API",
    input_schema={
        "url": {"type": "string", "required": True, "description": "请求 URL"},
        "method": {"type": "string", "default": "GET"},
        "headers": {"type": "object", "default": {}},
        "body": {"type": "object"},
        "timeout": {"type": "int", "default": 30},
    },
    execute=_http_request,
)


# ─── LLM 调用工具 ───

async def _llm_call(params: dict) -> dict:
    """执行 LLM 调用"""
    system_prompt = params.get("system_prompt", "")
    user_prompt = params.get("user_prompt", "")
    model = params.get("model", "deepseek-chat")
    max_tokens = params.get("max_tokens", 2000)
    temperature = params.get("temperature", 0.7)

    resp = _llm_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return {
        "content": resp.choices[0].message.content,
        "model": model,
        "usage": {
            "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
            "completion_tokens": resp.usage.completion_tokens if resp.usage else 0,
        }
    }


llm_tool = Tool(
    name="llm_call",
    description="调用大语言模型",
    input_schema={
        "system_prompt": {"type": "string", "required": True},
        "user_prompt": {"type": "string", "required": True},
        "model": {"type": "string", "default": "deepseek-chat"},
        "max_tokens": {"type": "int", "default": 2000},
        "temperature": {"type": "float", "default": 0.7},
    },
    execute=_llm_call,
)


# ─── Ledger 记账工具 ───

async def _ledger_record(params: dict) -> dict:
    """写入 Reliability Ledger"""
    r = requests.post("http://localhost:7003/api/ledger/record", json={
        "from_agent": params.get("from_agent", "unknown"),
        "to_agent": params.get("to_agent", "unknown"),
        "site_id": params.get("site_id", "slot-auto"),
        "action": params.get("action", "execute"),
        "tokens_used": params.get("tokens_used", 0),
        "success": params.get("success", True),
    }, timeout=10)
    return r.json()


ledger_tool = Tool(
    name="ledger_record",
    description="写入 Agent 间交易账本",
    input_schema={
        "from_agent": {"type": "string", "required": True},
        "to_agent": {"type": "string", "required": True},
        "site_id": {"type": "string", "default": "slot-auto"},
        "action": {"type": "string", "required": True},
        "tokens_used": {"type": "int", "default": 0},
        "success": {"type": "bool", "default": True},
    },
    execute=_ledger_record,
)


# ─── 注册到全局 Registry ───

def register_builtin_tools():
    reg = get_tool_registry()
    reg.register(http_tool)
    reg.register(llm_tool)
    reg.register(ledger_tool)

    # 绑定能力到工具
    reg.bind_to_capability("search_collector", ["http_request", "llm_call"])
    reg.bind_to_capability("article_writer", ["llm_call"])
    reg.bind_to_capability("data_analyst", ["llm_call"])
    reg.bind_to_capability("researcher", ["http_request", "llm_call"])
    reg.bind_to_capability("summarizer", ["llm_call"])
    reg.bind_to_capability("translator", ["llm_call"])
    reg.bind_to_capability("code_writer", ["llm_call"])
    reg.bind_to_capability("ledger", ["ledger_record"])
