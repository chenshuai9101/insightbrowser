#!/usr/bin/env bash
# ============================================================
# InsightLabs 一键启动脚本（v2）
# 启动：Registry / Hosting / AHP / Reliability / InsightSee /
#       InsightHub / Commerce / InsightLens(HTTP) / Content
#
# 路径可通过环境变量覆盖（默认假定各仓库平级存放）：
#   IB_REGISTRY_DIR  insightbrowser 仓库路径（默认本脚本所在目录）
#   IB_HOSTING_DIR   insightbrowser-hosting 仓库路径
#   IB_AHP_DIR       AHP 代理路径（默认 $IB_REGISTRY_DIR/insightbrowser-ahp）
#   IB_RELIABILITY_DIR 可靠性服务路径（默认 $IB_REGISTRY_DIR/insightbrowser-reliability）
#   IB_COMMERCE_DIR  Commerce 路径（默认 $IB_REGISTRY_DIR/insightbrowser-commerce）
#   IB_SEE_DIR       insightsee 仓库路径
#   IB_HUB_DIR       insighthub 仓库路径
#   IB_LENS_DIR      insightlens 仓库路径
#   IB_CONTENT_DIR   insightbrowser-content 仓库路径
#
# 其他：
#   KILL_PORTS=1     启动前先杀掉占用端口的旧进程（默认不杀）
#   PORT_PREFIX=71   端口前缀（默认 70，即 7000/7001/...；便于多实例测试）
# ============================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
LOGDIR="${LOGDIR:-$ROOT/.logs}"
mkdir -p "$LOGDIR"

REGISTRY_DIR="${IB_REGISTRY_DIR:-$ROOT}"
HOSTING_DIR="${IB_HOSTING_DIR:-$(dirname "$ROOT")/insightbrowser-hosting}"
SEE_DIR="${IB_SEE_DIR:-$(dirname "$ROOT")/insightsee}"
HUB_DIR="${IB_HUB_DIR:-$(dirname "$ROOT")/insighthub}"
LENS_DIR="${IB_LENS_DIR:-$(dirname "$ROOT")/insightlens}"
CONTENT_DIR="${IB_CONTENT_DIR:-$(dirname "$ROOT")/insightbrowser-content}"
AHP_DIR="${IB_AHP_DIR:-$REGISTRY_DIR/insightbrowser-ahp}"
RELIABILITY_DIR="${IB_RELIABILITY_DIR:-$REGISTRY_DIR/insightbrowser-reliability}"
COMMERCE_DIR="${IB_COMMERCE_DIR:-$REGISTRY_DIR/insightbrowser-commerce}"

# 端口前缀：默认 70 -> 7000/7001/...，可用 PORT_PREFIX=71 变更为 7100/7101/...
PREFIX="${PORT_PREFIX:-70}"
PORT_REGISTRY="${PREFIX}00"
PORT_HOSTING="${PREFIX}01"
PORT_AHP="${PREFIX}02"
PORT_RELIABILITY="${PREFIX}03"
PORT_COMMERCE="${PREFIX}04"
PORT_LENS="${PREFIX}91"
PORT_CONTENT="${PREFIX}24"

require_dir() {
  [ -d "$1" ] || { echo "❌ 目录不存在: $1（请用 IB_*_DIR 指定仓库路径）"; exit 1; }
}

require_dir "$REGISTRY_DIR"
require_dir "$HOSTING_DIR"
require_dir "$SEE_DIR"
require_dir "$HUB_DIR"
require_dir "$LENS_DIR"
require_dir "$CONTENT_DIR"
require_dir "$AHP_DIR"
require_dir "$RELIABILITY_DIR"
require_dir "$COMMERCE_DIR"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  🏢 InsightLabs — 启动所有服务（v2）                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"

if [ "${KILL_PORTS:-0}" = "1" ]; then
  echo "🧹 清理旧进程..."
  for port in "$PORT_REGISTRY" "$PORT_HOSTING" "$PORT_AHP" "$PORT_RELIABILITY" "$PORT_COMMERCE" "$PORT_LENS" "$PORT_CONTENT"; do
    pid=$(lsof -ti :"$port" 2>/dev/null || true) && kill "$pid" 2>/dev/null && echo "  端口 $port 已释放" || true
  done
  sleep 1
fi

start_service() {
  local name="$1" dir="$2" port="$3" cmd="$4"
  echo "  [$name] → :$port"
  ( cd "$dir" && eval "$cmd" > "$LOGDIR/$name.log" 2>&1 & echo $! > "$LOGDIR/$name.pid" )
  for _ in $(seq 1 30); do
    if lsof -ti :"$port" >/dev/null 2>&1; then
      echo "       ✅ $name 运行中 (pid $(cat "$LOGDIR/$name.pid"))"
      return 0
    fi
    sleep 1
  done
  echo "       ❌ $name 启动失败"; tail -5 "$LOGDIR/$name.log"; return 1
}

start_service "registry"    "$REGISTRY_DIR"    "$PORT_REGISTRY"    "INSIGHTBROWSER_PORT=$PORT_REGISTRY python3 main.py"
start_service "hosting"     "$HOSTING_DIR"     "$PORT_HOSTING"     "INSIGHTBROWSER_HOSTING_PORT=$PORT_HOSTING INSIGHTBROWSER_REGISTRY_URL=http://127.0.0.1:$PORT_REGISTRY python3 main.py"
start_service "ahp"         "$AHP_DIR"         "$PORT_AHP"         "python3 main.py"
start_service "reliability" "$RELIABILITY_DIR" "$PORT_RELIABILITY" "python3 main.py"
start_service "insightsee"  "$SEE_DIR"         "9090"              "python3 api_server.py"
start_service "insighthub"  "$HUB_DIR"         "8080"              "python3 main.py"
start_service "commerce"    "$COMMERCE_DIR"    "$PORT_COMMERCE"    "python3 run.py"
start_service "insightlens" "$LENS_DIR"        "$PORT_LENS"        "INSIGHTLENS_HTTP_PORT=$PORT_LENS python3 -m insightlens --http"
start_service "content"     "$CONTENT_DIR"     "$PORT_CONTENT"     "python3 main.py"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ 全部服务已启动                                          ║"
echo "║  Registry     → http://localhost:$PORT_REGISTRY   (服务目录) ║"
echo "║  Hosting      → http://localhost:$PORT_HOSTING   (站点托管)  ║"
echo "║  AHP Proxy    → http://localhost:$PORT_AHP       (Agent 协议)║"
echo "║  Reliability  → http://localhost:$PORT_RELIABILITY (信任)    ║"
echo "║  InsightSee   → http://localhost:9090            (需求洞察)  ║"
echo "║  InsightHub   → http://localhost:8080            (企业面板)  ║"
echo "║  Commerce     → http://localhost:$PORT_COMMERCE   (商家入驻) ║"
echo "║  InsightLens  → http://localhost:$PORT_LENS       (提取 HTTP)║"
echo "║  Content      → http://localhost:$PORT_CONTENT     (AEP 内容)║"
echo "║  日志: $LOGDIR                                         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
