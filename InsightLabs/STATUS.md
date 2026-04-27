# InsightLabs 项目状态

> 更新时间: 2026-04-26 09:15
> CEO: 牧云野（全权推进）
> 帅哥: 待通知完成

---

## 🏢 架构总览

```
┌─────────────────────────────────────────────────────┐
│  L3: Trust & Credit Layer (7003)                    │
│  ├─ Reliability Registry → 心跳/评级/排行榜        │
│  └─ Credit Ledger → 账本/交易/余额                  │
├─────────────────────────────────────────────────────┤
│  L2: Agent Interaction Layer (7002 + SDK)           │
│  ├─ AHP Proxy → agent.json / info / action / stream │
│  └─ Agent SDK → discover / call / stream / register  │
├─────────────────────────────────────────────────────┤
│  L1: Information Layer (7000 / 7001 / 9090 / 8080)  │
│  ├─ Registry → 站点注册/发现/搜索                    │
│  ├─ Hosting → 站点创建/管理/套餐                      │
│  ├─ InsightSee → 18行业/884关键词/6维度               │
│  └─ InsightHub → SaaS 管理面板                        │
└─────────────────────────────────────────────────────┘
```

## 状态

### L1 信息层 ✅ 100%
| 组件 | 端口 | 状态 |
|:----|:---:|:----:|
| InsightLens (MCP) | — | 6工具，注册到 OpenClaw MCP |
| Registry | 7000 | 注册/发现/搜索/统计 |
| Hosting | 7001 | 站点创建/套餐/agent.json |
| InsightSee | 9090 | 18行业/884关键词 |
| InsightHub | 8080 | SaaS 管理后台 |

### L2 交互层 ✅ 100%
| 组件 | 端口 | 状态 |
|:----|:---:|:----:|
| AHP Proxy | 7002 | agent.json/info/action/data/stream |
| Agent SDK | — | discover/call/stream/register |
| 端到端验证 | — | 搜索→发现→agent.json→info→action→stream |

### L3 信任+经济层 ✅ 100%
| 组件 | 端口 | 状态 |
|:----|:---:|:----:|
| Reliability Registry | 7003 | 心跳(30s)/评级(S/A/B/C/D)/排行榜 |
| Credit Ledger | 7003 | 积分(1000初始)/交易/余额/审计 |
| SDK min_rating | — | 按评级过滤搜索 |
| AHP 集成 | 7002 | 站点列表含信任评级 |

## 运行端口
- Registry: 7000 ✅
- Hosting: 7001 ✅
- AHP Proxy: 7002 ✅
- Reliability: 7003 ✅
- InsightSee: 9090 ✅
- InsightHub: 8080 ✅

## 一键启动
`start-insightlabs.sh` — 启动全部 6 个服务
