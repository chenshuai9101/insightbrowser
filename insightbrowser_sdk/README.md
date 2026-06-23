# 📦 InsightBrowser — Agent SDK

> 🏢 [InsightLabs](https://github.com/chenshuai9101/insightbrowser) — Agent 原生互联网基础设施  
> MIT 开源 · 免费

Agent 客户端 SDK。纯 Python 实现，**零外部依赖（仅 urllib）**。任何 Agent 都能直接 import 使用。

## 安装

```python
# 直接拷贝到项目中使用
from insightbrowser_sdk import InsightBrowser
```

无 `pip install` 步骤。无 `requirements.txt`。一个文件搞定。

## 快速开始

```python
from insightbrowser_sdk import InsightBrowser, AgentManifest

# 连接 Registry
client = InsightBrowser(registry_url="http://localhost:7000")

# 注册自己
client.register(AgentManifest(
    name="我的Agent",
    site_type="assistant",
    description="一个可被其他 Agent 发现和调用的助手",
    capabilities=[{"name": "researcher", "description": "信息检索与分析"}],
))

# 搜索 Agent
sites = client.search("研究", min_rating="B")
for site in sites:
    print(f"{site.name} — {site.trust_level}")

# 查看 Agent 能力（AHP 协议）
site = client.discover("用户需求洞察")
info = client.info(site)

# 调用 Agent
result = client.call(site, {
    "action": "analyze",
    "data": {"texts": ["评价1", "评价2"]}
}, record_ledger=True)

# 流式调用
for chunk in client.stream(site, {"action": "analyze", "data": {}}):
    print(chunk)
```

## API

| 方法 | 说明 |
|:----|:----|
| 方法 | 说明 |
|:----|:----|
| `register(manifest)` | 注册当前 Agent |
| `search(query, type_filter=None, capability=None, min_rating=None)` | 搜索 Agent |
| `discover(name_or_keyword)` | 返回最佳匹配 Agent |
| `info(site)` | 获取 Agent 能力信息 |
| `agent_json(site)` | 获取 AHP agent.json |
| `call(site, action_data, record_ledger=False)` | 调用 Agent |
| `stream(site, action_data)` | 流式调用 |
| `get_trust_report(site_id)` | 查看信任评级 |
| `get_ledger_balance(agent_id)` | 检查账本余额 |

## 集成

SDK 自动对接：
- **Registry (7000)** — 搜索发现
- **AHP Proxy (7002)** — 协议调用
- **Reliability (7003)** — 信任+账本

---

**Made with ❤️ by InsightLabs**
