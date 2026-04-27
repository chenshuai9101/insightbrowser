#!/usr/bin/env bash
# ============================================================
# InsightLabs 一键启动脚本
# 启动所有平台服务：AHP + Registry + Hosting + InsightSee + InsightHub + Reliability
# Port: 7002 / 7000 / 7001 / 9090 / 8080 / 7003
# ============================================================

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
LOGDIR="$ROOT/.logs"
mkdir -p "$LOGDIR"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  🏢 InsightLabs — 启动所有服务                             ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# 清理旧进程
echo "🧹 清理旧进程..."
for port in 7000 7001 7002 7003 7004 7005 9090 8080; do
    pid=$(lsof -ti :$port 2>/dev/null) && kill $pid 2>/dev/null && echo "  端口$port 已释放"
done
sleep 1

# 1. InsightBrowser Registry
echo ""
echo "  [1/6] 🔍 InsightBrowser Registry → :7000"
cd "$ROOT/insightbrowser"
python3 main.py > "$LOGDIR/registry.log" 2>&1 &
sleep 2
if lsof -ti :7000 >/dev/null 2>&1; then
    echo "       ✅ Registry 运行中"
else
    echo "       ❌ Registry 启动失败"
    tail -5 "$LOGDIR/registry.log"
    exit 1
fi

# 2. InsightBrowser Hosting
echo "  [2/6] 🌐 InsightBrowser Hosting → :7001"
cd "$ROOT/insightbrowser-hosting"
python3 main.py > "$LOGDIR/hosting.log" 2>&1 &
sleep 2
if lsof -ti :7001 >/dev/null 2>&1; then
    echo "       ✅ Hosting 运行中"
else
    echo "       ❌ Hosting 启动失败"
    tail -5 "$LOGDIR/hosting.log"
    exit 1
fi

# 3. InsightBrowser AHP Proxy
echo "  [3/6] 🔗 InsightBrowser AHP Proxy → :7002"
cd "$ROOT/InsightLabs/insightbrowser-ahp"
pip install -q -r requirements.txt 2>/dev/null || true
python3 main.py > "$LOGDIR/ahp.log" 2>&1 &
sleep 2
if lsof -ti :7002 >/dev/null 2>&1; then
    echo "       ✅ AHP Proxy 运行中"
else
    echo "       ❌ AHP Proxy 启动失败"
    tail -5 "$LOGDIR/ahp.log"
    exit 1
fi

# 4. InsightBrowser Reliability
echo "  [4/6] 🛡️ InsightBrowser Reliability → :7003"
cd "$ROOT/InsightLabs/insightbrowser-reliability"
pip install -q -r requirements.txt 2>/dev/null || true
python3 main.py > "$LOGDIR/reliability.log" 2>&1 &
sleep 2
if lsof -ti :7003 >/dev/null 2>&1; then
    echo "       ✅ Reliability 运行中（心跳检测每30s）"
else
    echo "       ❌ Reliability 启动失败"
    tail -5 "$LOGDIR/reliability.log"
    exit 1
fi

# 5. InsightSee API
echo "  [5/6] 🔎 InsightSee API → :9090"
cd "$ROOT/insightsee-skill"
python3 api_server.py > "$LOGDIR/insightsee.log" 2>&1 &
sleep 2
if lsof -ti :9090 >/dev/null 2>&1; then
    echo "       ✅ InsightSee 运行中"
else
    echo "       ❌ InsightSee 启动失败"
    tail -5 "$LOGDIR/insightsee.log"
    exit 1
fi

# 6. InsightHub Dashboard
echo "  [6/7] 📊 InsightHub Dashboard → :8080"
cd "$ROOT/insighthub"
python3 main.py > "$LOGDIR/insighthub.log" 2>&1 &
sleep 2
if lsof -ti :8080 >/dev/null 2>&1; then
    echo "       ✅ InsightHub 运行中"

# 7. Commerce Bridge
echo "  [7/8] 🏪 Commerce Bridge → :7004"
cd "$ROOT/InsightLabs/insightbrowser-commerce"
python3 run.py > "$LOGDIR/commerce.log" 2>&1 &
sleep 2
if lsof -ti :7004 >/dev/null 2>&1; then
    echo "       ✅ Commerce Bridge 运行中"
else
    echo "       ❌ Commerce Bridge 启动失败"
    tail -5 "$LOGDIR/commerce.log"
    exit 1
fi
else
    echo "       ❌ InsightHub 启动失败"
    tail -5 "$LOGDIR/insighthub.log"
    exit 1
fi

# 8. A-Hub Slots
cd "$ROOT/InsightLabs/insightbrowser-slots"
pip3 install -q fastapi uvicorn pydantic 2>/dev/null
echo "  [8/8] 🔲 A-Hub Slots → :7005"
python3 -c "import uvicorn, main; uvicorn.run(main.app, host='0.0.0.0', port=7005)" > "$LOGDIR/slots.log" 2>&1 &
sleep 2
if lsof -ti :7005 >/dev/null 2>&1; then
    echo "       ✅ Slots 卡槽系统 运行中"
else
    echo "       ❌ Slots 启动失败"
    tail -5 "$LOGDIR/slots.log"
    exit 1
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ 所有服务已启动                                        ║"
echo "║                                                              ║"
echo "║  Registry     → http://localhost:7000  (服务目录)           ║"
echo "║  Hosting      → http://localhost:7001  (站点托管)           ║"
echo "║  AHP Proxy    → http://localhost:7002  (Agent 协议)         ║"
echo "║  Reliability  → http://localhost:7003  (信任+账本)          ║"
echo "║  InsightSee   → http://localhost:9090  (需求洞察)           ║"
echo "║  InsightHub   → http://localhost:8080  (企业面板)           ║"
echo "║  Commerce     → http://localhost:7004  (商家入驻)           ║"
echo "║  A-Hub Slots  → http://localhost:7005  (卡槽系统)           ║"
echo "║                                                              ║"
echo "║  Agent SDK: insightbrowser_sdk/ (零依赖)                    ║"
echo "║  AHP 协议:  ahp/0.1                                        ║"
echo "║                                                              ║"
echo "║  日志目录: $LOGDIR                               ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# 快速自检
echo ""
echo "🧪 快速自检..."
for port in 7000 7001 7002 7003 7005 9090 8080; do
    status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/ 2>/dev/null || echo "ERR")
    case $port in
        7000) name="Registry" ;;
        7001) name="Hosting" ;;
        7002) name="AHP Proxy" ;;
        7003) name="Reliability" ;;
        9090) name="InsightSee" ;;
        8080) name="InsightHub" ;;
    esac
    if [ "$status" = "200" ] || [ "$status" = "307" ] || [ "$status" = "404" ]; then
        echo "  ✅ $name (:${port}) — HTTP $status"
    else
        echo "  ⚠️  $name (:${port}) — HTTP $status (可能仍在启动)"
    fi
done

echo ""
echo "🎉 InsightLabs 已就绪 — 端到端 Agent 互联网基础设施"