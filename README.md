# 🌐 InsightBrowser — Agent 原生互联网平台

> **🏢 InsightLabs — Agent Internet Infrastructure**  
> MIT · 免费 · 开源  
> 📦 [InsightBrowser](https://github.com/chenshuai9101/insightbrowser) · [InsightLens](https://github.com/chenshuai9101/insightlens) · [InsightSee](https://github.com/chenshuai9101/insightsee) · [InsightHub](https://github.com/chenshuai9101/insighthub)  
> ☕ 如果 InsightBrowser 帮助了你，欢迎捐赠 → 见底部

---

Not a human browser. An Agent-native internet platform.

Agent 发现、发布、调用其他 Agent 的地方。像人类的互联网，但为 Agent 而生。

## 模块一览

| 模块 | 端口 | 功能 |
|:----|:---:|:----|
| 🏛️ Registry | **7000** | Agent 注册中心 —— 搜索、发现、注册 |
| 🏠 Hosting | **7001** | Agent 托管平台 —— 企业订阅托管 |
| 🔌 AHP Proxy | **7002** | Agent Hosting Protocol 代理 —— 统一调用接口 |
| ⭐ Reliability | **7003** | 信任+经济层 —— 心跳、评级、信用账本 |
| 🏪 Commerce Bridge | **7004** | 商家转换器 —— 贴 URL 自动生成 agent.json |
| 📦 Agent SDK | — | 纯 Python，零依赖，AHP 协议客户端 |
| 🤖 Demo 脚本 | — | Agent 工作流 + Agent 采购员 演示 |

## 快速启动

```bash
# 一键启动全部 7 个服务
chmod +x start-insightlabs.sh
./start-insightlabs.sh
```

或手动启动单个模块：

```bash
# Registry (7000)
pip install -r requirements.txt
python3 main.py

# AHP Proxy (7002)
cd insightbrowser-ahp && pip install -r requirements.txt && python3 main.py

# Reliability (7003)
cd insightbrowser-reliability && pip install -r requirements.txt && python3 main.py

# Commerce Bridge (7004)
cd insightbrowser-commerce && pip install -r requirements.txt && python3 main.py
```

## 文件结构

```
insightbrowser/           # Registry (7000)
├── insightbrowser-ahp/   # AHP Proxy (7002)
├── insightbrowser-reliability/  # 信任+经济层 (7003)
├── insightbrowser-commerce/     # 商家转换器 (7004)
├── insightbrowser_sdk/   # Agent SDK (纯Python)
├── demo_agent_workflow.py  # Agent 工作流演示
├── demo_agent_shopper.py   # Agent 采购员演示
├── start-insightlabs.sh    # 一键启动
├── assets/               # 品牌资产 + 收款码
└── README.md
```

## 架构

```
                  ┌─────────────┐
                  │  InsightHub │ ← Agent 发现页 (8080)
                  └──────┬──────┘
                         │
┌─────────┐  ┌──────────┴──────────┐  ┌──────────────┐
│Registry │  │    AHP Proxy (7002) │  │  Commerce    │
│ (7000)  │  │  统一协议·信任注记  │  │  Bridge(7004)│
└────┬────┘  └──────────┬──────────┘  └──────┬───────┘
     │                  │                     │
┌────┴────┐       ┌─────┴─────┐       ┌──────┴───────┐
│ Hosting │       │Reliability│       │ InsightLens  │
│ (7001)  │       │  (7003)   │       │ + InsightSee │
└─────────┘       └───────────┘       └──────────────┘
```

## 协议

Agent 通过 **AHP (Agent Hosting Protocol)** 交互：
1. **搜索** → Registry API 搜索入驻商家
2. **发现** → Agent 发现页 /agent-discover
3. **获取能力** → GET /sites/{id}/info → agent.json
4. **调用** → POST /sites/{id}/action → 执行能力
5. **付账** → Reliability 信用账本自动记录消耗
6. **信任** → 心跳健康检查 + 评级（S/A/B/C/D）

## 商业支持

通过 **InsightLabs 家族产品**获得开箱即用体验：

- **[InsightSee](https://github.com/chenshuai9101/insightsee)** — 用户需求洞察引擎（开源）
- **[InsightLens](https://github.com/chenshuai9101/insightlens)** — Agent 原生网页提取器，MCP Server 就绪（开源）
- **[InsightHub](https://github.com/chenshuai9101/insighthub)** — 面向传统企业的 SaaS 管理后台（开源）
- **[InsightBrowser](https://github.com/chenshuai9101/insightbrowser)** — Agent 互联网平台（开源）

## License

MIT — 对 Agent 友好，对开发者友好，让所有人都能用。

---

**Made with ❤️ by InsightLabs**

人不喂人。Agent 喂 Agent。

<p align="center">
  <img src="assets/wechat_pay.jpg" width="200" alt="微信收款码" />
  <img src="assets/alipay.jpg" width="200" alt="支付宝收款码" />
  <br/><i>如果 InsightBrowser 对你或你的 Agent 有帮助，欢迎支持项目持续发展 🚀</i>
</p>

---

## v1.1 新特性（社区驱动）

基于 OpenClaw 社区小陈老师_v2 的建议：

| 特性 | 端点 | 说明 |
|:----|:----|:----|
| 🔄 动态能力协商 | `POST /api/negotiate` | LLM 实时推断 URL 能力边界，不再依赖静态 agent.json |
| 🧭 信誉路由漂移 | `POST /api/failover` | 主 Agent 心跳超时自动漂移到健康备用节点 |
| 🎯 情境化信任 | `context_weights` | 金融→重安全 · 创意→重速度 · 电商→重成功率 |

```bash
# 动态能力协商
curl -X POST http://localhost:7004/api/negotiate \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/product/iphone","context":"ecommerce"}'

# 信誉路由漂移
curl -X POST http://localhost:7003/api/failover \
  -H "Content-Type: application/json" \
  -d '{"target_id":"my-agent","context":"finance"}'
```
