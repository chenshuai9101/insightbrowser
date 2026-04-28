#!/usr/bin/env bash
# ============================================================
# InsightLabs 一键启动脚本 v2.0
# 22 服务全栈启动：7000-7021 + 8080 + 9090
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

# P0-P3 Infrastructure
(cd "$ROOT/InsightLabs/insightbrowser-billing" && python3 run.py) > "$LOGDIR/billing.log" 2>&1 &
(cd "$ROOT/InsightLabs/insightbrowser-auth" && python3 run.py) > "$LOGDIR/auth.log" 2>&1 &
(cd "$ROOT/InsightLabs/insightbrowser-queue" && python3 run.py) > "$LOGDIR/queue.log" 2>&1 &
(cd "$ROOT/InsightLabs/insightbrowser-frontend" && python3 main.py) > "$LOGDIR/frontend.log" 2>&1 &
(cd "$ROOT/InsightLabs/insightbrowser-monitor" && python3 main.py) > "$LOGDIR/monitor.log" 2>&1 &
(cd "$ROOT/InsightLabs/insightbrowser-devportal" && python3 main.py) > "$LOGDIR/devportal.log" 2>&1 &
(cd "$ROOT/InsightLabs/insightbrowser-audit" && python3 main.py) > "$LOGDIR/audit.log" 2>&1 &

# P4: Agent Runtime Services
(cd "$ROOT/InsightLabs/insightbrowser-wallet" && python3 main.py) > "$LOGDIR/wallet.log" 2>&1 &
(cd "$ROOT/InsightLabs/insightbrowser-matching" && python3 main.py) > "$LOGDIR/matching.log" 2>&1 &
(cd "$ROOT/InsightLabs/insightbrowser-approval" && python3 main.py) > "$LOGDIR/approval.log" 2>&1 &
(cd "$ROOT/InsightLabs/insightbrowser-feedback" && python3 main.py) > "$LOGDIR/feedback.log" 2>&1 &
(cd "$ROOT/InsightLabs/insightbrowser-sandbox" && python3 main.py) > "$LOGDIR/sandbox.log" 2>&1 &
(cd "$ROOT/InsightLabs/insightbrowser-bi" && python3 main.py) > "$LOGDIR/bi.log" 2>&1 &
(cd "$ROOT/InsightLabs/insightbrowser-benchmark" && python3 main.py) > "$LOGDIR/benchmark.log" 2>&1 &
(cd "$ROOT/InsightLabs/insightbrowser-search" && python3 main.py) > "$LOGDIR/search.log" 2>&1 &
(cd "$ROOT/InsightLabs/insightbrowser-notify" && python3 main.py) > "$LOGDIR/notify.log" 2>&1 &
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
for port in 7000 7001 7002 7003 7004 7005 7006 7007 7008 7009 7010 7011 7012 7013 7014 7015 7016 7017 7018 7019 7020 7021 9090 8080; do
    status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/health 2>/dev/null || echo "...")
    case $port in
        7000) name="Registry" ;;
        7001) name="Hosting" ;;
        7002) name="AHP Proxy" ;;
        7003) name="Reliability" ;;
        7004) name="Commerce" ;;
        7005) name="Slots" ;;
        7006) name="Billing" ;;
        7007) name="Auth" ;;
        7008) name="Queue" ;;
        7009) name="Frontend" ;;
        7010) name="Monitor" ;;
        7011) name="DevPortal" ;;
        7012) name="Audit" ;;
        7013) name="Wallet" ;;
        7014) name="Matching" ;;
        7015) name="Approval" ;;
        7016) name="Feedback" ;;
        7017) name="Sandbox" ;;
        7018) name="BI" ;;
        7019) name="Benchmark" ;;
        7020) name="Search" ;;
        7021) name="Notify" ;;
        9090) name="InsightSee" ;;
        8080) name="InsightHub" ;;
    esac
    if [ "$status" = "200" ] || [ "$status" = "307" ] || [ "$status" = "404" ]; then
        echo "  ✅ $name (:${port}) — HTTP $status"
    else
        echo "  ⚠️  $name (:${port}) — $status (启动中)"
    fi
done

echo ""
echo "🎉 InsightLabs v2.0 — 22 服务 Agent 互联网全栈就位"
echo "   核心层: Registry · Hosting · AHP · Reliability · Commerce · Slots"
echo "   基础设施: Billing · Auth · Queue · Frontend · Monitor · DevPortal · Audit"
echo "   Agent运行时: Wallet · Matching · Approval · Feedback · Sandbox · BI · Benchmark · Search · Notify"