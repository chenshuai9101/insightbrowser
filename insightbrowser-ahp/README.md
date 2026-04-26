# 🔌 InsightBrowser — AHP Proxy (端口 7002)

> 🏢 [InsightLabs](https://github.com/chenshuai9101/insightbrowser) — Agent 原生互联网基础设施  
> MIT 开源 · 免费

AHP (Agent Hosting Protocol) 协议代理引擎。统一对外暴露 Agent 调用接口，集成信任注记和引擎路由。

## 端口

- **AHP Proxy**: `localhost:7002`

## API

| 端点 | 方法 | 说明 |
|:----|:---:|:----|
| `/sites` | GET | 获取所有站点（含信任评级） |
| `/sites/{id}/agent.json` | GET | 获取 Agent 能力描述 |
| `/sites/{id}/info` | GET | 获取站点详细信息 |
| `/sites/{id}/action` | POST | 调用 Agent 执行行动 |
| `/sites/{id}/data` | GET | 获取原始数据 |
| `/sites/{id}/stream` | GET | 流式数据 |
| `/health` | GET | 健康检查 |

## 依赖

```bash
pip install -r requirements.txt
python3 main.py
```

## 集成

AHP Proxy 自动对接：
- **Registry (7000)** — 获取站点列表
- **Reliability (7003)** — 信任评级注入
- **InsightLens (通过 SDK)** — 网页提取
- **InsightSee (通过 SDK)** — 用户需求分析

---

**Made with ❤️ by InsightLabs**

<p align="center">
  <img src="https://raw.githubusercontent.com/chenshuai9101/insightbrowser/main/assets/wechat_pay.jpg" width="150" alt="微信" />
  <img src="https://raw.githubusercontent.com/chenshuai9101/insightbrowser/main/assets/alipay.jpg" width="150" alt="支付宝" />
  <br/><i>如果本项目有帮助，欢迎捐赠支持持续发展 ☕</i>
</p>
