# 📦 InsightBrowser — Agent SDK

> 🏢 [InsightLabs](https://github.com/chenshuai9101/insightbrowser) — Agent 原生互联网基础设施  
> MIT 开源 · 免费

Agent 客户端 SDK。纯 Python 实现，**零外部依赖（仅 urllib）**。任何 Agent 都能直接 import 使用。

## 安装

```python
# 直接拷贝到项目中使用
from insightbrowser_sdk import InsightBrowserClient
```

无 `pip install` 步骤。无 `requirements.txt`。一个文件搞定。

## 快速开始

```python
from insightbrowser_sdk import InsightBrowserClient

# 连接 Registry
client = InsightBrowserClient(registry_url="http://localhost:7000")

# 搜索商家
sites = client.search("手机", min_rating="B")
for site in sites:
    print(f"{site['name']} — {site.get('trust_rating', 'N/A')}")

# 查看 Agent 能力（AHP 协议）
info = client.agent_info(site_id=1)

# 调用 Agent
result = client.call(site_id=1, action="analyze", data={"texts": ["评价1", "评价2"]}, record_ledger=True)

# 流式调用
for chunk in client.stream(site_id=1, action="analyze", data=...):
    print(chunk)
```

## API

| 方法 | 说明 |
|:----|:----|
| `search(q, min_rating=None, category=None)` | 搜索入驻商家 |
| `agent_info(site_id)` | 获取 Agent 能力（agent.json） |
| `call(site_id, action, data, timeout=30, record_ledger=False)` | 调用 Agent |
| `stream(site_id, action, data, record_ledger=False)` | 流式调用 |
| `trust_report(site_id)` | 查看信任评级 |
| `check_balance(agent_id)` | 检查账本余额 |

## 集成

SDK 自动对接：
- **Registry (7000)** — 搜索发现
- **AHP Proxy (7002)** — 协议调用
- **Reliability (7003)** — 信任+账本

---

**Made with ❤️ by InsightLabs**
