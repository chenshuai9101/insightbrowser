"""InsightBrowser SDK — Data Models"""
from typing import Any, Optional


class Site:
    """Represents a discovered agent site."""

    def __init__(self, data: dict):
        self.site_id: str = data.get("site_id", data.get("id", ""))
        self.name: str = data.get("name", "")
        self.site_type: str = data.get("type", data.get("site_type", "general"))
        self.description: str = data.get("description", "")
        self.protocol: str = data.get("protocol", "ahp/0.1")
        self.endpoint: str = data.get("endpoint", "")
        self.trust_level: str = data.get("trust_level", "unverified")
        self.rating: float = float(data.get("rating", 0))
        self.usage_count: int = int(data.get("usage_count", 0))

        # AHP proxy info (when accessed through AHP proxy)
        self.ahp_endpoints: dict = data.get("ahp_endpoints", {})

        # Capabilities
        raw_caps = data.get("capabilities", [])
        self.capabilities: list[dict] = raw_caps

        # Source (where this site came from)
        self._source: str = data.get("_source", "registry")

    @property
    def capability_names(self) -> list[str]:
        return [c.get("name", "") for c in self.capabilities]

    @property
    def ahp_base(self) -> str:
        """Get the AHP base URL for this site.

        Prefers AHP proxy endpoint, falls back to direct endpoint.
        """
        if self.ahp_endpoints:
            info_url = self.ahp_endpoints.get("info", "")
            if info_url:
                # Extract base from the info URL
                return info_url.replace("/info", "")
        return self.endpoint

    def __repr__(self) -> str:
        return f"Site(id={self.site_id}, name='{self.name}', type={self.site_type})"


class AgentManifest:
    """Agent manifest for self-registration."""

    def __init__(self, name: str, site_type: str = "general",
                 description: str = "", capabilities: Optional[list] = None,
                 endpoint: str = "", owner: str = ""):
        self.protocol: str = "ahp/0.1"
        self.name: str = name
        self.type: str = site_type
        self.description: str = description
        self.capabilities: list = capabilities or []
        self.endpoint: str = endpoint
        self.owner: str = owner
        self.trust_level: str = "self-registered"

    def to_dict(self) -> dict:
        return {
            "protocol": self.protocol,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "capabilities": self.capabilities,
            "endpoint": self.endpoint,
            "owner": self.owner,
            "trust_level": self.trust_level,
        }


class ActionRequest:
    """AHP action request payload."""

    def __init__(self, action: str, data: Any = None,
                 action_type: str = ""):
        self.action: str = action
        self.data: dict = data if isinstance(data, dict) else {}
        if action_type:
            self.data["type"] = action_type

    def to_dict(self) -> dict:
        result = {"action": self.action}
        if self.data:
            result["data"] = self.data
        return result


class ActionResponse:
    """AHP action response."""

    def __init__(self, data: dict):
        self.raw: dict = data
        self.success: bool = data.get("success", False)
        self.protocol: str = data.get("protocol", "")
        self.action: str = data.get("action", "")
        self.data: Any = data.get("data")
        self.error: Optional[str] = data.get("error")

    def __repr__(self) -> str:
        if self.success:
            return f"ActionResponse(success=True, action='{self.action}')"
        return f"ActionResponse(success=False, error='{self.error}')"
