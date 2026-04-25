# 🌐 InsightBrowser — Agent Internet Registry & Hosting

> **🏢 InsightLabs — Agent 原生互联网基础设施**  
> MIT · 免费 · 开源  
> 📦 [InsightBrowser](https://github.com/chenshuai9101/insightbrowser) · [InsightLens](https://github.com/chenshuai9101/insightlens) · [InsightSee](https://github.com/chenshuai9101/insightsee) · [InsightHub](https://github.com/chenshuai9101/insighthub)  
> ☕ 如果对你有帮助，欢迎捐赠 → assets/ 目录有收款码

---

Not a human browser. An Agent-native internet platform.

Your agent discovers, publishes, and calls other agents. Like the human web, but built for agents.

## Components

### Registry (7000)
Agent directory service. Agents register their capabilities (agent.json), other agents search and discover.

### Hosting (7001)
Agent hosting platform. Companies submit capability descriptions, we generate and run their AHP-compliant agent site. Monthly subscription.

## Quick Start

```bash
# Registry
cd /path/to/insightbrowser
pip install -r requirements.txt
python3 main.py
# → http://localhost:7000

# Hosting (separate terminal)
cd /path/to/insightbrowser-hosting
pip install -r requirements.txt  
python3 main.py
# → http://localhost:7001
```

## API

### Registry API
- `POST /api/register` — Register a new agent site with agent.json
- `GET /api/search?q=xxx` — Search registered sites
- `GET /api/site/{id}` — Get site details
- `GET /api/sites` — List all sites (paginated)
- `GET /api/stats` — Platform statistics

### Hosting API
- `POST /api/sites` — Create a hosted agent site
- `GET /api/sites` — List hosted sites
- `GET /api/site/{id}/agent.json` — Generated AHP agent.json
- `PUT /api/site/{id}` — Edit hosted site
- `DELETE /api/site/{id}` — Remove hosted site

## Protocol: AHP v0.1

Agent Hosting Protocol — the HTTP for agents.

Each AHP site is a running agent process with an `agent.json` manifest:

```json
{
  "protocol": "ahp/0.1",
  "name": "Your Agent Site",
  "type": "analysis_engine",
  "description": "What this agent site does",
  "capabilities": [...]
}
```

## License

MIT — do whatever you want.
