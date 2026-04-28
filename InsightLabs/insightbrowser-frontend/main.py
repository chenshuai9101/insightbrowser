"""
InsightBrowser Frontend — 需求入口前端
端口: 7009
"""
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import requests
import re

app = FastAPI(title="InsightBrowser Frontend", version="1.0.0")

CHAT_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>InsightLabs — Agent 互联网</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f172a;color:#e2e8f0;height:100vh;display:flex;flex-direction:column}
header{background:#1e293b;padding:16px 24px;border-bottom:1px solid #334155;display:flex;align-items:center;gap:12px}
header h1{font-size:20px;color:#38bdf8}
header span{font-size:12px;color:#64748b}
.chat-area{flex:1;overflow-y:auto;padding:24px;display:flex;flex-direction:column;gap:16px}
.msg{max-width:80%;padding:14px 18px;border-radius:16px;line-height:1.6;font-size:15px;animation:fadeIn .3s}
.msg.user{align-self:flex-end;background:#2563eb;color:#fff;border-bottom-right-radius:4px}
.msg.agent{align-self:flex-start;background:#1e293b;border:1px solid #334155;border-bottom-left-radius:4px}
.msg.agent pre{background:#0f172a;padding:12px;border-radius:8px;overflow-x:auto;margin:8px 0;font-size:13px}
.msg.system{align-self:center;background:transparent;color:#64748b;font-size:12px;padding:4px}
.input-area{padding:16px 24px;background:#1e293b;border-top:1px solid #334155;display:flex;gap:12px}
.input-area input{flex:1;padding:14px 18px;border-radius:24px;border:1px solid #475569;background:#0f172a;color:#e2e8f0;font-size:15px;outline:none;transition:border .2s}
.input-area input:focus{border-color:#38bdf8}
.input-area button{background:#2563eb;color:#fff;border:none;padding:14px 28px;border-radius:24px;font-size:15px;cursor:pointer;transition:background .2s}
.input-area button:hover{background:#1d4ed8}
.input-area button:disabled{opacity:.5;cursor:not-allowed}
.status-bar{padding:8px 24px;background:#1e293b;border-top:1px solid #334155;font-size:12px;color:#64748b;display:flex;justify-content:space-between}
@keyframes fadeIn{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}
</style>
</head>
<body>
<header><h1>🔗 InsightLabs</h1><span>Agent 互联网 需求入口</span></header>
<div class="chat-area" id="chat">
<div class="msg agent">
👋 我是牧云野，InsightLabs CEO。<br>
对说一句话，我会自动拆解任务、调用 Agent 网络、交给你最终结果。<br><br>
💡 试试这些：<br>
• 调研AI Agent电商最新趋势，写投资人简报<br>
• 帮我分析5个竞争对手的定价策略<br>
• 帮我生成一篇关于医药反腐的深度文章
</div>
</div>
<div class="input-area">
<input id="input" placeholder="说说你想做什么..." onkeydown="if(event.key==='Enter')send()">
<button id="sendBtn" onclick="send()">发送</button>
</div>
<div class="status-bar">
<span id="status">🟢 11 服务在线</span>
<span id="timer"></span>
</div>
<script>
const chat=document.getElementById('chat');
const input=document.getElementById('input');
const sendBtn=document.getElementById('sendBtn');
const statusEl=document.getElementById('status');
const timerEl=document.getElementById('timer');
let startTime;

function addMsg(text,role){
  const div=document.createElement('div');
  div.className='msg '+role;
  div.textContent=text;
  chat.appendChild(div);
  chat.scrollTop=chat.scrollHeight;
}

async function send(){
  const text=input.value.trim();
  if(!text) return;
  addMsg(text,'user');
  input.value='';
  sendBtn.disabled=true;
  startTime=Date.now();
  statusEl.textContent='🟡 处理中...';

  addMsg('🔍 正在拆解任务...','system');
  addMsg('⚙️ 正在调用 Agent 网络...','system');

  const resp=await fetch('/api/v1/frontend/query',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({query:text})
  });

  const data=await resp.json();
  const elapsed=((Date.now()-startTime)/1000).toFixed(0);
  timerEl.textContent=elapsed+'s';

  if(data.success){
    statusEl.textContent='🟢 交付完成';
    addMsg('📦 '+data.summary,'agent');
    if(data.delivery){
      addMsg(data.delivery,'agent');
    }
    addMsg('⏱ 总耗时 '+elapsed+'s | 🔗 Ledger: '+data.ledger_count+' 笔交易','system');
  }else{
    statusEl.textContent='🔴 '+data.error;
    addMsg('❌ '+data.error,'agent');
  }
  sendBtn.disabled=false;
  input.focus();
}

// Check service health
fetch('/api/v1/frontend/health').then(r=>r.json()).then(d=>{
  statusEl.textContent=d.all_online?'🟢 '+d.count+' 服务在线':'🔴 部分离线';
});
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return CHAT_HTML


@app.get("/api/v1/frontend/health")
async def health():
    services = {
        "registry": 7000, "hosting": 7001, "ahp": 7002, "reliability": 7003,
        "commerce": 7004, "slots": 7005, "billing": 7006, "auth": 7007,
        "queue": 7008, "insighthub": 8080, "insightsee": 9090,
    }
    online = 0
    details = {}
    for name, port in services.items():
        try:
            r = requests.get(f"http://localhost:{port}/", timeout=2)
            details[name] = r.status_code == 200
            if r.status_code == 200:
                online += 1
        except:
            details[name] = False
    return {"count": online, "total": len(services), "all_online": online == len(services), "details": details}


@app.post("/api/v1/frontend/query")
async def query(req: Request):
    data = await req.json()
    query_text = data.get("query", "")

    # 1. 提交到队列
    try:
        r = requests.post("http://localhost:7008/api/v1/queue/submit", json={
            "user_request": query_text,
            "priority": 3,
            "agent_id": "frontend-user",
        }, timeout=5)
        task = r.json()
        task_id = task.get("task_id", "unknown")
    except Exception as e:
        return {"success": False, "error": f"队列提交失败: {e}"}

    # 2. 直接调 Slots 流水线获取结果
    try:
        r = requests.post("http://localhost:7005/api/v1/slots/pipeline", json={
            "user_request": query_text,
            "max_steps": 20,
        }, timeout=300)
        result = r.json()
    except Exception as e:
        return {"success": False, "error": f"流水线执行失败: {e}"}

    if not result.get("success"):
        return {"success": False, "error": result.get("error", "执行失败")}

    synthesis = result.get("synthesis", {})
    verification = result.get("verification", {})
    content = synthesis.get("content", "")

    # 3. 记录到 Ledger
    try:
        requests.post("http://localhost:7003/api/ledger/record", json={
            "from_agent": "frontend-user",
            "to_agent": "slots-pipeline",
            "site_id": task_id,
            "action": "human_entry_query",
            "tokens_used": len(content),
            "success": True,
        }, timeout=5)
    except:
        pass

    summary = f"✅ 交付物已完成 | 质量评分: {verification.get('total_score', 'N/A')}/100"
    preview = content[:800] + ("..." if len(content) > 800 else "")

    return {
        "success": True,
        "task_id": task_id,
        "summary": summary,
        "delivery": preview,
        "verification": verification,
        "ledger_count": 1,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7009)
