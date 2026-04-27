"""
InsightBrowser Slots — A-Hub 卡槽系统
=========================================
A-Hub 核心架构：五大卡槽，Agent 通过卡槽接入生态。

五大卡槽：
1. 感知卡槽 (Perception)  - 接收信息、解析意图、理解需求
2. 规划卡槽 (Planning)    - 任务拆分、策略制定、路径规划
3. 执行卡槽 (Execution)   - 调用能力、执行操作、完成任务
4. 合成卡槽 (Synthesis)   - 汇总结果、结构化输出、质量检查
5. 验证卡槽 (Verification) - 结果校验、质量评分、信任更新

每个卡槽都通过标准 AHP 协议暴露，可被任何 Agent 调用。
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="InsightBrowser Slots - A-Hub 卡槽系统", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

from routes import slots

app.include_router(slots.router, prefix="/api/v1/slots")

@app.get("/")
def root():
    return {
        "service": "InsightBrowser Slots",
        "version": "1.0.0",
        "description": "A-Hub 卡槽系统 - Agent 能力接入的标准化接口",
        "slots": {
            "perception": {"path": "/api/v1/slots/perceive", "description": "感知：理解需求"},
            "planning": {"path": "/api/v1/slots/plan", "description": "规划：拆分任务"},
            "execution": {"path": "/api/v1/slots/execute", "description": "执行：调用能力"},
            "synthesis": {"path": "/api/v1/slots/synthesize", "description": "合成：汇总结果"},
            "verification": {"path": "/api/v1/slots/verify", "description": "验证：质量检查"},
        },
        "metrics": {"path": "/api/v1/slots/metrics", "description": "卡槽使用统计"},
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7005, reload=True)
