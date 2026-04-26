"""InsightBrowser AHP - Data Models

AHP v0.1 Protocol data models for agent site representation.
"""
from typing import Any, Optional
from datetime import datetime


# ─── Hosting Site Model (from Hosting API) ────────────────────────────

class HostingSite:
    """Represents a site hosted on InsightBrowser Hosting (port 7001)."""

    def __init__(self, data: dict):
        self.id: int = data.get("id")
        self.name: str = data.get("name", "")
        self.site_type: str = data.get("site_type", "other")
        self.description: str = data.get("description", "")
        self.status: str = data.get("status", "running")
        self.plan: str = data.get("plan", "free")
        self.owner: str = data.get("owner", "default")
        self.call_count: int = data.get("call_count", 0)
        self.data_source: str = data.get("data_source", "manual")
        self.data_config: Any = data.get("data_config", {})
        self.created_at: str = data.get("created_at", "")
        self.updated_at: str = data.get("updated_at", "")

        # Parse capabilities
        raw_caps = data.get("capabilities", [])
        if isinstance(raw_caps, str):
            import json
            raw_caps = json.loads(raw_caps)
        self.capabilities: list = raw_caps

        # Parse agent_json
        raw_agent = data.get("agent_json")
        if raw_agent and isinstance(raw_agent, str):
            import json
            try:
                raw_agent = json.loads(raw_agent)
            except json.JSONDecodeError:
                raw_agent = None
        self.agent_json: Optional[dict] = raw_agent

    @property
    def is_active(self) -> bool:
        return self.status == "running"

    @property
    def ahp_type(self) -> str:
        """Return the AHP agent type based on site_type or capabilities."""
        if self.site_type in ("insightsee", "analysis"):
            return "insightsee"
        if self.site_type in ("insightlens", "extraction", "scraper"):
            return "insightlens"
        return self.site_type

    def to_agent_json(self) -> dict:
        """Generate an agent.json compliant with AHP v0.1."""
        return {
            "protocol": "ahp/0.1",
            "name": self.name,
            "type": self.ahp_type,
            "description": self.description,
            "capabilities": [
                {
                    "id": cap.get("id", f"cap_{i}"),
                    "name": cap.get("name", "Unnamed"),
                    "description": cap.get("description", ""),
                    "params": cap.get("parameters", []),
                    "returns": "json"
                }
                for i, cap in enumerate(self.capabilities)
            ],
            "meta": {
                "site_id": f"hosted-{self.id}",
                "hosted_by": "InsightBrowser Hosting",
                "ahp_proxy": f"http://localhost:7002/sites/{self.id}",
                "status": self.status,
                "plan": self.plan,
                "call_count": self.call_count,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            }
        }


# ─── AHP Response Models ──────────────────────────────────────────────

class AHPInfo:
    """AHP Info response — describes capabilities, pricing, version."""

    def __init__(self, site: HostingSite):
        self.protocol: str = "ahp/0.1"
        self.name: str = site.name
        self.type: str = site.ahp_type
        self.description: str = site.description
        self.version: str = "1.0.0"
        self.capabilities: list = [
            {
                "id": cap.get("id", f"cap_{i}"),
                "name": cap.get("name", "Unnamed"),
                "description": cap.get("description", ""),
            }
            for i, cap in enumerate(site.capabilities)
        ]
        self.rate_limit: str = "100/hour" if site.plan == "free" else "unlimited"
        self.pricing: dict = {
            "plan": site.plan,
            "per_call": 0 if site.plan == "free" else 0,  # all free for now
        }

    def to_dict(self) -> dict:
        return {
            "protocol": self.protocol,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "version": self.version,
            "capabilities": self.capabilities,
            "rate_limit": self.rate_limit,
            "pricing": self.pricing,
        }


class AHPActionRequest:
    """AHP /action request body."""

    def __init__(self, data: dict):
        self.action: str = data.get("action", "")
        self.type: str = data.get("type", "")
        self.data: Any = data.get("data", {})

    def is_valid(self) -> bool:
        return bool(self.action or self.type)


class AHPActionResponse:
    """AHP /action response."""

    def __init__(self, success: bool, data: Any = None,
                 error: Optional[str] = None, action: str = ""):
        self.success: bool = success
        self.data: Any = data
        self.error: Optional[str] = error
        self.action: str = action
        self.protocol: str = "ahp/0.1"

    def to_dict(self) -> dict:
        result = {
            "protocol": self.protocol,
            "success": self.success,
            "action": self.action,
        }
        if self.data is not None:
            result["data"] = self.data
        if self.error:
            result["error"] = self.error
        return result


class AHPDataResponse:
    """AHP /data response."""

    def __init__(self, success: bool, data: Any = None, total: int = 0,
                 message: str = ""):
        self.success: bool = success
        self.data: Any = data
        self.total: int = total
        self.message: str = message

    def to_dict(self) -> dict:
        result = {
            "protocol": "ahp/0.1",
            "success": self.success,
            "total": self.total,
        }
        if self.data is not None:
            result["data"] = self.data
        if self.message:
            result["message"] = self.message
        return result
