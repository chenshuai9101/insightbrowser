# InsightLabs 项目状态（维护版）

> 更新时间: 2026-08-18（由自动化审查更新）
> 本表如实反映“可运行”与“规划中”，避免把骨架当作成品对外宣称。

## 可运行服务（能启动、有路由）

| 组件 | 端口 | 状态 | 说明 |
|:----|:---:|:----:|:----|
| Registry | 7000 | ✅ | 注册/发现/搜索/统计/Profile/虾条/RPC 调用/反馈/信誉 |
| Hosting | 7001 | ✅ | 站点创建/套餐/agent.json/注册 Registry//action 端点 |
| AHP Proxy | 7002 | ✅ | agent.json/info/action/data/stream（代理层） |
| Reliability | 7003 | ✅ | 心跳/评级/账本（L3 信任层） |
| Commerce | 7004 | ✅ | 商家入驻网关 |
| InsightSee | 9090 | ✅ | 需求解码（关键词规则 + 可选 LLM） |
| InsightHub | 8080 | ✅ | SaaS 面板（接 InsightLens/InsightSee，失败显式降级 mock） |
| InsightLens | 9091(HTTP) | ✅ | 网页提取 MCP + HTTP 服务 |
| Content | 7024 | ✅ | AEP/1.0 内容层 |

## 骨架 / 规划中（有 main.py 但路由未实现，勿宣称可用）

approval · audit · auth · benchmark · bi · billing · devportal · feedback ·
frontend · matching · monitor · notify · queue · sandbox · search · slots · wallet

> 说明：这些目录只有入口文件，import 的路由模块尚不存在，启动即失败。
> 上线前请先实现核心路由，或从对外文档中移除“22 个微服务”的表述。

## 已知待办（P0）

- [x] Registry: SSRF 拦截、call/feedback 端点补全、X-Agent-Key 鉴权
- [x] Hosting: owner key 鉴权、套餐服务端分配、Registry 注册链路修复
- [x] InsightLens: 默认校验 TLS、新增 HTTP 服务层
- [x] InsightHub: 真实调用 InsightLens/InsightSee、签名会话、显式 mock 标记
- [ ] 公网部署时设置 INSIGHTBROWSER_STRICT_SSRF=1 与 INSIGHTHUB_SECRET
- [ ] 清理 InsightLabs/ 与顶层重复代码（保留单一源码位置）

## 一键启动

`start-insightlabs.sh` — 启动 9 个服务（路径可用 IB_*_DIR 环境变量覆盖）。
