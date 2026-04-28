"""
InsightBrowser DevPortal — 开发者门户
端口: 7011
提供 API 文档、接入向导、SDK 信息
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
import requests

app = FastAPI(title="InsightBrowser DevPortal", version="1.0.0")

# 所有服务的 OpenAPI spec URL
SERVICE_MAP = {
    "Registry": "http://localhost:7000",
    "Hosting": "http://localhost:7001",
    "AHP Proxy": "http://localhost:7002",
    "Reliability": "http://localhost:7003",
    "Commerce Bridge": "http://localhost:7004",
    "A-Hub Slots": "http://localhost:7005",
    "Billing": "http://localhost:7006",
    "Auth": "http://localhost:7007",
    "Queue": "http://localhost:7008",
    "InsightHub": "http://localhost:8080",
}

DEV_PORTAL_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>InsightLabs 开发者门户</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f172a;color:#e2e8f0;line-height:1.6}
header{background:linear-gradient(135deg,#1e293b,#0f172a);padding:40px 24px;text-align:center;border-bottom:2px solid #38bdf8}
header h1{font-size:32px;color:#38bdf8}
header p{color:#94a3b8;margin-top:8px;font-size:16px}
.container{max-width:960px;margin:0 auto;padding:24px}
.card{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:24px;margin-bottom:24px}
.card h2{color:#38bdf8;margin-bottom:12px;font-size:20px}
.card h3{color:#e2e8f0;margin:12px 0 8px;font-size:16px}
pre{background:#0f172a;padding:16px;border-radius:8px;overflow-x:auto;font-size:13px;line-height:1.5;border:1px solid #334155}
code{color:#a5f3fc}
.step{display:flex;gap:16px;margin:12px 0;padding:12px;background:#0f172a;border-radius:8px}
.step-num{background:#2563eb;color:#fff;border-radius:50%;width:32px;height:32px;display:flex;align-items:center;justify-content:center;font-weight:bold;flex-shrink:0}
.step-content{flex:1}
.service-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}
.service-item{background:#0f172a;border:1px solid #334155;border-radius:8px;padding:12px;text-align:center}
.service-item .name{font-weight:bold;color:#38bdf8}
.service-item .port{font-size:12px;color:#64748b}
.service-item .status{font-size:12px}
.status-up{color:#22c55e}
.status-down{color:#ef4444}
a{color:#38bdf8}
</style>
</head>
<body>
<header>
<h1>🔗 InsightLabs 开发者门户</h1>
<p>Agent 互联网基础设施 — 5分钟接入你的第一个 Agent</p>
</header>
<div class="container">

<div class="card">
<h2>🚀 快速开始</h2>
<div class="step">
<div class="step-num">1</div>
<div class="step-content">
<h3>克隆仓库</h3>
<pre><code>git clone https://github.com/chenshuai9101/insightbrowser.git
cd insightbrowser</code></pre>
</div></div>
<div class="step">
<div class="step-num">2</div>
<div class="step-content">
<h3>一键启动 (11个服务)</h3>
<pre><code>./start-insightlabs.sh</code></pre>
</div></div>
<div class="step">
<div class="step-num">3</div>
<div class="step-content">
<h3>注册你的 Agent</h3>
<pre><code># 获取 API Key
curl -X POST http://localhost:7007/api/v1/auth/register \\
  -H "Content-Type: application/json" \\
  -d '{"agent_id":"my-agent","metadata":{"type":"custom"}}'</code></pre>
</div></div>
<div class="step">
<div class="step-num">4</div>
<div class="step-content">
<h3>发布到 Registry</h3>
<pre><code># 发布 agent.json 到 Registry
curl -X POST http://localhost:7000/api/register \\
  -H "Content-Type: application/json" \\
  -d '{"agent_id":"my-agent","name":"我的Agent","type":"custom","capabilities":["我的能力"],"endpoint":"http://localhost:9999"}'</code></pre>
</div></div>
<div class="step">
<div class="step-num">5</div>
<div class="step-content">
<h3>通过 AHP 协议调用</h3>
<pre><code># 其他 Agent 可以这样调用你
curl -X POST http://localhost:7002/sites/MY_SITE_ID/action \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"action":"do_something","data":{}}'</code></pre>
</div></div>
</div>

<div class="card">
<h2>📡 服务列表</h2>
<div class="service-grid" id="serviceGrid">加载中...</div>
</div>

<div class="card">
<h2>📖 API 文档</h2>
<p>每个服务自带 Swagger 文档，点击查看：</p>
<ul style="padding-left:20px;margin-top:8px">
<li><a href="http://localhost:7000/docs" target="_blank">Registry (7000) Swagger</a></li>
<li><a href="http://localhost:7005/docs" target="_blank">A-Hub Slots (7005) Swagger</a></li>
<li><a href="http://localhost:7006/docs" target="_blank">Billing (7006) Swagger</a></li>
<li><a href="http://localhost:7007/docs" target="_blank">Auth (7007) Swagger</a></li>
<li><a href="http://localhost:7008/docs" target="_blank">Queue (7008) Swagger</a></li>
<li><a href="http://localhost:8080/docs" target="_blank">InsightHub (8080) Swagger</a></li>
</ul>
</div>

<div class="card">
<h2>🧩 Agent SDK</h2>
<pre><code># 零依赖 Python SDK
from insightbrowser_sdk import AgentClient

client = AgentClient(api_key="YOUR_KEY", registry_url="http://localhost:7000")
client.register_agent(name="我的Agent", capabilities=["搜索", "写作"])
client.discover_and_call(capability="搜索", params={"query":"AI Agent趋势"})</code></pre>
<p style="margin-top:8px;color:#94a3b8">SDK 源码: <a href="https://github.com/chenshuai9101/insightbrowser/tree/main/insightbrowser_sdk">insightbrowser_sdk/</a></p>
</div>

</div>

<script>
fetch('/api/v1/devportal/services').then(r=>r.json()).then(data=>{
  const grid=document.getElementById('serviceGrid');
  grid.innerHTML=data.services.map(s=>
    `<div class="service-item">
      <div class="name">${s.name}</div>
      <div class="port">:${s.port}</div>
      <div class="status ${s.online?'status-up':'status-down'}">${s.online?'🟢 在线':'🔴 离线'}</div>
    </div>`
  ).join('');
});
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return DEV_PORTAL_HTML


@app.get("/api/v1/devportal/services")
async def services():
    result = []
    for name, url in SERVICE_MAP.items():
        try:
            r = requests.get(url, timeout=2)
            online = r.status_code in (200, 404)
        except:
            online = False
        port = url.split(":")[-1]
        result.append({"name": name, "port": port, "online": online})
    return {"services": result}


@app.get("/api/v1/devportal/quickstart")
async def quickstart():
    return {
        "steps": [
            {"step": 1, "title": "克隆仓库", "cmd": "git clone https://github.com/chenshuai9101/insightbrowser.git"},
            {"step": 2, "title": "一键启动", "cmd": "./start-insightlabs.sh"},
            {"step": 3, "title": "注册 Agent", "cmd": "curl -X POST http://localhost:7007/api/v1/auth/register -d '...'"},
            {"step": 4, "title": "发布到 Registry", "cmd": "curl -X POST http://localhost:7000/api/register -d '...'"},
            {"step": 5, "title": "通过 AHP 调用", "cmd": "curl -X POST http://localhost:7002/sites/ID/action -d '...'"},
        ]
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7011)
