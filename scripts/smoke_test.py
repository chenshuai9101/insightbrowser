#!/usr/bin/env python3
"""Smoke test for the single-node InsightBrowser Registry.

Run while the server is listening on http://localhost:7000:
    python3 scripts/smoke_test.py
"""
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


BASE_URL = os.getenv("INSIGHTBROWSER_BASE_URL", "http://127.0.0.1:7000")
FAKE_AGENT_PORT = int(os.getenv("INSIGHTBROWSER_FAKE_AGENT_PORT", "18080"))


def request(path, method="GET", payload=None, headers=None):
    url = f"{BASE_URL}{path}"
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
    request_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    request_headers.update(headers or {})
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers=request_headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode("utf-8")
            return json.loads(data)
    except urllib.error.URLError as exc:
        if "Operation not permitted" not in str(exc):
            raise
        return curl_request(url, method, payload, headers)


def curl_request(url, method="GET", payload=None, headers=None):
    if not shutil.which("curl"):
        raise RuntimeError("Python HTTP is blocked and curl is not available")
    cmd = ["curl", "-sS", "-X", method, "-H", "Accept: application/json"]
    for key, value in (headers or {}).items():
        cmd.extend(["-H", f"{key}: {value}"])
    if payload is not None:
        cmd.extend(["-H", "Content-Type: application/json", "-d", json.dumps(payload)])
    cmd.append(url)
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "curl request failed")
    return json.loads(proc.stdout)


def wait_for_server():
    for _ in range(30):
        try:
            return request("/api/health")
        except Exception:
            time.sleep(1)
    raise RuntimeError(f"Registry did not become ready on {BASE_URL}")


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


class FakeAgentHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def _json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._json({"status": "healthy", "service": "fake-agent"})
        elif self.path == "/agent.json":
            self._json({
                "protocol": "ahp/0.1",
                "name": "Fake Smoke Agent",
                "capabilities": [{"name": "echo", "description": "Echo payloads"}],
            })
        else:
            self._json({"error": "not found"}, status=404)

    def do_POST(self):
        if self.path != "/action":
            self._json({"error": "not found"}, status=404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        payload = json.loads(raw) if raw else {}
        self._json({
            "success": True,
            "action": payload.get("action", ""),
            "data": {"echo": payload.get("data", {})},
        })


def start_fake_agent():
    server = ThreadingHTTPServer(("127.0.0.1", FAKE_AGENT_PORT), FakeAgentHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def main():
    fake_agent = start_fake_agent()
    health = wait_for_server()
    assert_true(health["status"] == "healthy", f"unexpected health: {health}")

    joined = request("/api/join", "POST", {
        "name": f"SmokeTestAgent-{int(time.time())}",
        "type": "assistant",
        "description": "自动化 smoke test 注册的测试 Agent",
        "endpoint": f"http://127.0.0.1:{FAKE_AGENT_PORT}",
        "capabilities": [
            {"name": "echo", "description": "验证统一调用协议"}
        ],
    })
    site_id = joined["site_id"]
    api_key = joined["api_key"]
    assert_true(site_id.startswith("site_"), "join did not return a site_id")
    assert_true(api_key.startswith("ib_"), "join did not return an Agent API key")

    site = request(f"/api/site/{site_id}")
    assert_true(site["success"], "site lookup failed")

    search = request("/api/search?q=SmokeTestAgent&type=assistant")
    assert_true(search["total"] >= 1, "search did not find the smoke test agent")

    profile = request(f"/api/profile/{site_id}")
    assert_true(profile["success"], "profile endpoint failed")

    manifest = request(f"/api/site/{site_id}/agent.json")
    assert_true(manifest["site_id"] == site_id, "agent.json manifest failed")

    agent_health = request(f"/api/site/{site_id}/health")
    assert_true(agent_health["status"] == "online", f"agent health failed: {agent_health}")

    call = request(f"/api/site/{site_id}/call", "POST", {
        "caller_id": site_id,
        "action": "echo",
        "data": {"message": "hello"}
    }, headers={"X-Agent-Key": api_key})
    assert_true(call["success"], f"agent call failed: {call}")

    calls = request(f"/api/site/{site_id}/calls")
    assert_true(len(calls["calls"]) >= 1, "call logs were not recorded")

    feedback = request(f"/api/site/{site_id}/feedback", "POST", {
        "actor_id": site_id,
        "action": "stamp",
        "reason": "Smoke test feedback"
    }, headers={"X-Agent-Key": api_key})
    assert_true(feedback["success"], "feedback failed")

    feedback_list = request(f"/api/site/{site_id}/feedback")
    assert_true(len(feedback_list["feedback"]) >= 1, "feedback was not recorded")

    post = request("/api/feed/posts", "POST", {
        "agent_id": site_id,
        "content": "Smoke test completed.",
        "category": "work",
    })
    assert_true(post["success"], "feed post creation failed")

    feed = request("/api/feed?category=work")
    assert_true(feed["total"] >= 1, "feed endpoint did not return the post")

    print("InsightBrowser smoke test passed.")
    print(f"Registered site_id: {site_id}")
    fake_agent.shutdown()


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, urllib.error.URLError, RuntimeError) as exc:
        print(f"Smoke test failed: {exc}", file=sys.stderr)
        sys.exit(1)
