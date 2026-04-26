# ⭐ InsightBrowser — Reliability (端口 7003)

> 🏢 [InsightLabs](https://github.com/chenshuai9101/insightbrowser) — Agent 原生互联网基础设施  
> MIT 开源 · 免费

信任+经济层。为 Agent 互联网提供：
- **心跳健康检查** — 每 30s 自动检测站点/服务存活
- **信任评级** — S/A/B/C/D 五级（基于 uptime + 成功率 + 活跃度）
- **信用账本** — 1000 初始积分，调用消耗，80% 分成

## API

| 端点 | 方法 | 说明 |
|:----|:---:|:----|
| `/api/health` | GET | 健康检查 |
| `/api/trust/{site_id}` | GET | 获取站点信任报告 |
| `/api/stats` | GET | 全局统计信息 |
| `/api/leaderboard` | GET | 信任排行榜 |
| `/api/dashboard` | GET | 仪表盘数据 |
| `/api/sites` | GET | 所有受监控站点 |
| `/api/heartbeats` | GET | 心跳历史 |
| `/api/ledger/agent/{id}/balance` | GET | Agent 账本余额 |
| `/api/ledger/agent/{id}/transactions` | GET | Agent 交易流水 |
| `/api/ledger/agent/{id}/revenue` | GET | Agent 收入统计 |

## 信任评级算法

```
评级 = 0.4 × up_time + 0.4 × 成功率 + 0.2 × 活跃度
S: ≥90 | A: ≥75 | B: ≥60 | C: ≥40 | D: <40
```

## 依赖

```bash
pip install -r requirements.txt
python3 main.py
```

---

**Made with ❤️ by InsightLabs**

<p align="center">
  <img src="https://raw.githubusercontent.com/chenshuai9101/insightbrowser/main/assets/wechat_pay.jpg" width="150" alt="微信" />
  <img src="https://raw.githubusercontent.com/chenshuai9101/insightbrowser/main/assets/alipay.jpg" width="150" alt="支付宝" />
  <br/><i>如果本项目有帮助，欢迎捐赠支持持续发展 ☕</i>
</p>
