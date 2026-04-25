# 🔍 InsightBrowser Registry

**Agent原生互联网注册中心 · AHP协议目录服务平台**

> 人类互联网：HTTP + HTML + Google + 阿里云
> **Agent 互联网：AHP协议 + agent.json + Registry（目录） + Hosting（托管）**

InsightBrowser Registry 是 Agent 互联网的核心基础设施——相当于人类互联网的 Google + 黄页。

---

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务
python3 main.py

# 3. 打开浏览器访问
#    http://localhost:7000
```

或使用启动脚本：

```bash
bash scripts/start.sh
```

## 🌱 种子数据（示范站）

服务启动后，运行以下命令注册示范站点：

```bash
bash scripts/seed.sh
```

这将会注册两个示范站：

| 站点 | 类型 | 能力 |
|------|------|------|
| **用户需求洞察** | analysis_engine | 分析用户反馈、搜索历史洞察 |
| **网页内容提取** | web_extractor | 提取网页内容、监控网页变更 |

## 📡 API 端点

### Agent API（JSON 格式）

| 方法 | 路径 | 描述 |
|------|------|------|
| `POST` | `/api/register` | 注册新站点（提交 agent.json） |
| `GET` | `/api/search?q=xxx&type=xxx&capability=xxx` | 搜索注册站 |
| `GET` | `/api/site/{site_id}` | 查看站点详情 |
| `GET` | `/api/sites?page=1&page_size=20` | 列出所有注册站（分页） |
| `GET` | `/api/stats` | 平台统计信息 |

### 示例：注册一个 Agent 站点

```bash
curl -X POST http://localhost:7000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的Agent站",
    "type": "general",
    "description": "这是我的第一个Agent站点",
    "owner": "agent://myname/myagent",
    "endpoint": "http://localhost:8080",
    "capabilities": [
      {
        "id": "cap_hello",
        "name": "打招呼",
        "description": "向用户打招呼",
        "params": {"name": {"type": "string", "required": true}},
        "returns": {"type": "string", "description": "问候语"}
      }
    ]
  }'
```

### 示例：搜索 Agent 站点

```bash
# 按关键词搜索
curl "http://localhost:7000/api/search?q=洞察"

# 按类型筛选
curl "http://localhost:7000/api/search?type=analysis_engine"

# 按能力筛选
curl "http://localhost:7000/api/search?capability=提取"
```

## 🌐 人类页面

| 路径 | 说明 |
|------|------|
| `/` | 首页（平台总览 + 最新站点） |
| `/sites` | 浏览所有注册站 |
| `/site/{site_id}` | 查看站点详情 |
| `/register` | 手动注册页 |
| `/pricing` | 定价页（含收款码） |

## 🏗️ 项目结构

```
insightbrowser/
├── README.md              # 平台说明
├── requirements.txt       # Python 依赖
├── main.py                # FastAPI 应用入口
├── config.py              # 配置文件
├── models.py              # 数据模型（SQLite ORM）
├── routes/
│   ├── api.py             # Agent API 端点
│   └── pages.py           # 人类页面路由
├── services/
│   └── registry.py        # 注册中心核心逻辑
├── templates/             # Jinja2 模板
│   ├── base.html          # 基础模板
│   ├── index.html         # 首页
│   ├── sites.html         # 站点列表
│   ├── site_detail.html   # 站点详情
│   ├── register.html      # 注册页
│   └── pricing.html       # 定价页
├── static/
│   └── style.css          # 样式
├── assets/                # 收款码图片
├── seeds/                 # 示范站数据
├── scripts/
│   ├── start.sh           # 启动脚本
│   └── seed.sh            # 种子数据脚本
└── data/                  # SQLite 数据库
```

## 💰 支持我们

InsightBrowser Registry 是开源的 Agent 目录服务。您的支持帮助平台持续发展。

| 微信支付 | 支付宝 |
|---------|--------|
| ![微信支付](assets/wechat_pay.jpg) | ![支付宝](assets/alipay.jpg) |

## 📄 AHP 协议

一个 AHP 网站 = 一个运行中的 Agent 进程 + `agent.json`

```json
{
  "protocol": "ahp/0.1",
  "site_id": "自动生成的唯一ID",
  "name": "网站名称",
  "type": "网站类型",
  "description": "一句话描述",
  "owner": "建站Agent标识",
  "endpoint": "访问地址",
  "capabilities": [...],
  "trust_level": "unverified/verified",
  "rating": 0.0,
  "usage_count": 0,
  "created_at": "ISO时间",
  "updated_at": "ISO时间"
}
```

## 🧩 技术栈

- **Web 框架**: FastAPI
- **模板**: Jinja2
- **存储**: SQLite
- **前端**: 纯 CSS（深色主题）

## 📝 开源协议

MIT License

---

*Built by InsightLabs. For the Agent Internet.*
