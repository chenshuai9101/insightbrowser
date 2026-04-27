"""InsightBrowser SDK — Main Client

Pure Python, zero external dependencies. Uses urllib for all HTTP.

Usage:
    from insightbrowser_sdk import InsightBrowser

    ib = InsightBrowser(registry_url="http://localhost:7000")

    # Discover sites
    sites = ib.search("用户需求洞察")
    site = ib.discover("InsightSee")

    # Call a site's capability
    result = ib.call(site, {
        "action": "analyze",
        "data": {"texts": ["产品不错但太贵"]}
    })
"""
import json
import logging
from typing import Any, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from .models import Site, ActionResponse, AgentManifest
from .errors import (
    InsightBrowserError,
    SiteNotFoundError,
    ActionError,
    ConnectionError,
)

logger = logging.getLogger("insightbrowser.sdk")

# ─── Default URLs ─────────────────────────────────────────────────────

DEFAULT_REGISTRY_URL = "http://localhost:7000"
DEFAULT_AHP_PROXY_URL = "http://localhost:7002"
DEFAULT_RELIABILITY_URL = "http://localhost:7003"


# ─── InsightBrowser Client ────────────────────────────────────────────

class InsightBrowser:
    """Main SDK client for discovering and calling agent sites."""

    def __init__(self, registry_url: str = DEFAULT_REGISTRY_URL,
                 ahp_proxy_url: str = DEFAULT_AHP_PROXY_URL,
                 reliability_url: str = DEFAULT_RELIABILITY_URL):
        self.registry_url = registry_url.rstrip("/")
        self.ahp_proxy_url = ahp_proxy_url.rstrip("/")
        self.reliability_url = reliability_url.rstrip("/")

    # ── HTTP Helpers (zero deps, pure urllib) ──────────────────────

    @staticmethod
    def _json_request(url: str, method: str = "GET",
                      body: Any = None,
                      timeout: int = 30) -> dict:
        """Make a JSON HTTP request using only urllib."""
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")

        req = Request(
            url,
            data=data,
            method=method,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "InsightBrowser-SDK/1.0",
            },
        )

        try:
            with urlopen(req, timeout=timeout) as resp:
                resp_body = resp.read().decode("utf-8")
                return json.loads(resp_body)
        except HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            try:
                error_data = json.loads(error_body)
            except json.JSONDecodeError:
                error_data = {"detail": error_body}
            raise ActionError(
                message=str(e),
                status_code=e.code,
                response_data=error_data,
            )
        except URLError as e:
            raise ConnectionError(f"Cannot connect to {url}: {e.reason}")
        except Exception as e:
            raise ConnectionError(f"Request failed: {e}")

    def _ahp_request(self, path: str, method: str = "GET",
                     body: Any = None, timeout: int = 30) -> dict:
        """Make a request to the AHP proxy."""
        url = f"{self.ahp_proxy_url}{path}"
        return self._json_request(url, method, body, timeout)

    def _registry_request(self, path: str, method: str = "GET",
                          body: Any = None, timeout: int = 30) -> dict:
        """Make a request to the Registry."""
        url = f"{self.registry_url}{path}"
        return self._json_request(url, method, body, timeout)

    def _reliability_request(self, path: str, method: str = "GET",
                             body: Any = None, timeout: int = 30) -> dict:
        """Make a request to the Reliability Registry (port 7003)."""
        url = f"{self.reliability_url}{path}"
        return self._json_request(url, method, body, timeout)

    # ── Registry Operations ────────────────────────────────────────

    def search(self, query: str = "", type_filter: str = "",
               capability: str = "", page: int = 1,
               page_size: int = 20, min_rating: str = "",
               trust_level: str = "") -> list[Site]:
        """Search the Registry for sites matching criteria.

        Args:
            query: Search keyword
            type_filter: Filter by site type
            capability: Filter by capability name
            page: Page number
            page_size: Results per page
            min_rating: Minimum trust rating (S/A/B/C/D) — filters via
                        Reliability Registry
            trust_level: Filter by trust level (verified/unverified)

        Returns:
            List of Site objects matching criteria
        """
        params = []
        if query:
            params.append(f"q={_urlencode(query)}")
        if type_filter:
            params.append(f"type_filter={_urlencode(type_filter)}")
        if capability:
            params.append(f"capability={_urlencode(capability)}")
        if trust_level:
            params.append(f"trust_level={_urlencode(trust_level)}")
        params.append(f"page={page}")
        params.append(f"page_size={page_size}")

        url = f"/api/search?{'&'.join(params)}"
        data = self._registry_request(url)

        sites_raw = data.get("sites", [])
        sites = [Site(s) for s in sites_raw]
        for s in sites:
            s._source = "registry"

        # Apply min_rating filter via Reliability Registry
        if min_rating and sites:
            sites = self._filter_by_min_rating(sites, min_rating)

        return sites

    def search_with_rating(self, query: str = "", type_filter: str = "",
                           capability: str = "", min_rating: str = "A",
                           page: int = 1, page_size: int = 20) -> list[Site]:
        """Search for sites with a minimum trust rating filter.

        Convenience wrapper around search() that defaults to min_rating="A".
        Only returns sites that meet the minimum reliability rating.

        Args:
            query: Search keyword
            type_filter: Filter by site type
            capability: Filter by capability
            min_rating: Minimum rating (S/A/B/C/D, default A)
            page: Page number
            page_size: Results per page

        Returns:
            List of sites meeting rating criteria
        """
        return self.search(
            query=query,
            type_filter=type_filter,
            capability=capability,
            page=page,
            page_size=page_size,
            min_rating=min_rating,
        )

    def _filter_by_min_rating(self, sites: list[Site],
                              min_rating: str) -> list[Site]:
        """Filter sites by minimum trust rating from Reliability Registry."""
        rating_order = {"S": 0, "A": 1, "B": 2, "C": 3, "D": 4}
        min_order = rating_order.get(min_rating.upper(), 4)

        filtered = []
        for site in sites:
            try:
                report = self._reliability_request(
                    f"/api/trust/{site.site_id}"
                )
                trust = report.get("trust_report", {})
                site_rating = trust.get("rating", "D")
                site_order = rating_order.get(site_rating, 4)
                if site_order <= min_order:
                    # Enrich site with trust data
                    site.trust_level = site_rating
                    site.rating = trust.get("score", 0)
                    filtered.append(site)
            except Exception:
                # If reliability registry is unavailable, include site
                # with a default rating
                filtered.append(site)

        return filtered

    def discover(self, name_or_keyword: str,
                 limit: int = 5) -> Optional[Site]:
        """Discover a site by name or keyword.

        Returns the best match, or None if nothing found.
        """
        sites = self.search(query=name_or_keyword)

        if not sites:
            # Try searching by type
            sites = self.search(capability=name_or_keyword)

        if not sites:
            # Try AHP proxy site list
            try:
                proxy_data = self._ahp_request("/sites")
                proxied_sites = proxy_data.get("sites", [])
                for s in proxied_sites:
                    if (name_or_keyword.lower() in s.get("name", "").lower()
                            or name_or_keyword.lower() in s.get("description",
                                                                "").lower()):
                        sites.append(Site(s))
                        break
                if not sites and proxied_sites:
                    sites.append(Site(proxied_sites[0]))
            except Exception as e:
                logger.warning(f"AHP proxy discovery failed: {e}")

        if not sites:
            return None

        # Return the best match (exact name match gets priority)
        for s in sites:
            if s.name.lower() == name_or_keyword.lower():
                return s

        return sites[0]

    def register(self, manifest: AgentManifest) -> dict:
        """Register an agent site with the Registry."""
        data = self._registry_request(
            "/api/register",
            method="POST",
            body=manifest.to_dict(),
        )
        return data

    # ── AHP Operations ─────────────────────────────────────────────

    def info(self, site: Site) -> dict:
        """Get detailed info about a site via AHP."""
        if site.ahp_endpoints:
            info_url = site.ahp_endpoints.get("info", "")
            if info_url:
                # Build full URL from endpoint
                return self._ahp_request(f"/sites/{site.site_id}/info")

        # Fallback: try registry lookup
        data = self._registry_request(f"/api/site/{site.site_id}")
        return data.get("site", data)

    def call(self, site: Site, action_data: dict,
             timeout: int = 60,
             record_ledger: bool = False,
             caller_id: str = "insightbrowser-sdk",
             tokens_used: int = 0) -> ActionResponse:
        """Call a site's capability via AHP action endpoint.

        Args:
            site: The Site object to call
            action_data: dict with 'action' and optional 'data' keys
            timeout: Request timeout in seconds
            record_ledger: If True, records the call in the credit ledger
            caller_id: Agent ID for ledger tracking
            tokens_used: Estimated tokens consumed (for credit cost)

        Returns:
            ActionResponse object
        """
        site_id = self._resolve_site_id(site)
        try:
            data = self._ahp_request(
                f"/sites/{site_id}/action",
                method="POST",
                body=action_data,
                timeout=timeout,
            )
            success = data.get("success", False)

            # Record in credit ledger if requested
            if record_ledger:
                try:
                    self._reliability_request(
                        "/api/ledger/record",
                        method="POST",
                        body={
                            "from_agent": caller_id,
                            "to_agent": site.name,
                            "site_id": str(site_id),
                            "action": action_data.get("action", "call"),
                            "tokens_used": tokens_used,
                            "success": success,
                        },
                    )
                except Exception as e:
                    logger.warning(f"Failed to record ledger transaction: {e}")

            return ActionResponse(data)
        except Exception as e:
            # Record failed call in ledger
            if record_ledger:
                try:
                    self._reliability_request(
                        "/api/ledger/record",
                        method="POST",
                        body={
                            "from_agent": caller_id,
                            "to_agent": site.name,
                            "site_id": str(site_id),
                            "action": action_data.get("action", "call"),
                            "tokens_used": tokens_used,
                            "success": False,
                        },
                    )
                except Exception:
                    pass
            raise

    def stream(self, site: Site, action_data: dict,
               timeout: int = 120) -> list[dict]:
        """Call a site's capability via SSE stream (synchronous wrapper).

        Args:
            site: The Site object to call
            action_data: dict with 'action' and optional 'data' keys
            timeout: Request timeout in seconds

        Returns:
            List of SSE event data dicts
        """
        import urllib.parse

        site_id = self._resolve_site_id(site)

        # Build query params
        params = {
            "action": action_data.get("action", "query"),
            "type": action_data.get("data", {}).get("type", ""),
            "data": json.dumps(action_data.get("data", {})),
        }
        query_string = urllib.parse.urlencode(params)
        url = f"{self.ahp_proxy_url}/sites/{site_id}/stream?{query_string}"

        events = []
        req = Request(
            url,
            headers={
                "Accept": "text/event-stream",
                "User-Agent": "InsightBrowser-SDK/1.0",
            },
        )

        try:
            with urlopen(req, timeout=timeout) as resp:
                buffer = b""
                while True:
                    chunk = resp.read(4096)
                    if not chunk:
                        break
                    buffer += chunk
                    # Parse SSE events from buffer
                    decoded = buffer.decode("utf-8")
                    for line in decoded.split("\n"):
                        if line.startswith("data: "):
                            event_data = line[6:]
                            if event_data.strip():
                                try:
                                    events.append(json.loads(event_data))
                                except json.JSONDecodeError:
                                    events.append({"raw": event_data})
                    buffer = b""
        except Exception as e:
            logger.warning(f"Stream error: {e}")

        return events

    def agent_json(self, site: Site) -> dict:
        """Get the agent.json manifest for a site."""
        site_id = self._resolve_site_id(site)
        return self._ahp_request(f"/sites/{site_id}")

    def site_data(self, site: Site, filters: dict = None) -> dict:
        """Get data from a site."""
        site_id = self._resolve_site_id(site)
        body = {}
        if filters:
            body["filters"] = filters
        return self._ahp_request(
            f"/sites/{site_id}/data",
            method="POST",
            body=body,
        )

    def list_proxied_sites(self, min_rating: str = "") -> list[Site]:
        """List all sites available through the AHP proxy.

        Args:
            min_rating: Optional minimum trust rating filter (S/A/B/C/D)

        Returns:
            List of Site objects
        """
        data = self._ahp_request("/sites")
        raw_sites = data.get("sites", [])
        sites = [Site(s) for s in raw_sites]

        if min_rating:
            sites = self._filter_by_min_rating(sites, min_rating)

        return sites

    # ── Reliability Operations ──────────────────────────────────────

    def get_trust_report(self, site_id: str) -> dict:
        """Get the trust report for a site from Reliability Registry."""
        return self._reliability_request(f"/api/trust/{site_id}")

    def get_reliability_stats(self) -> dict:
        """Get global reliability statistics."""
        return self._reliability_request("/api/stats")

    def get_reliability_leaderboard(self,
                                    min_rating: str = "") -> dict:
        """Get the site trust leaderboard."""
        path = "/api/leaderboard"
        if min_rating:
            path += f"?min_rating={min_rating}"
        return self._reliability_request(path)

    def get_ledger_balance(self, agent_id: str) -> dict:
        """Get an agent's credit balance."""
        return self._reliability_request(
            f"/api/ledger/agent/{agent_id}/balance"
        )

    def get_ledger_transactions(self, agent_id: str = "",
                                limit: int = 50) -> dict:
        """Get transaction history."""
        if agent_id:
            path = f"/api/ledger/agent/{agent_id}?limit={limit}"
        else:
            path = f"/api/ledger/transactions?limit={limit}"
        return self._reliability_request(path)

    def get_dashboard(self) -> dict:
        """Get the management dashboard data."""
        return self._reliability_request("/api/dashboard")

    # ── Helpers ────────────────────────────────────────────────────

    def _resolve_site_id(self, site: Site) -> str:
        """Resolve a site's ID for AHP proxy calls.

        For Registry sites (string IDs like 'site_...'), looks up
        by name in the AHP proxy's site list.
        """
        sid = str(site.site_id)
        if sid.startswith("site_") or not sid.isdigit():
            if site.ahp_endpoints:
                info_url = site.ahp_endpoints.get("info", "")
                if info_url:
                    parts = info_url.split("/")
                    for p in parts:
                        if p.isdigit():
                            return p
            try:
                data = self._ahp_request("/sites")
                for s in data.get("sites", []):
                    if s.get("name", "").lower() == site.name.lower():
                        return str(s["id"])
            except Exception:
                pass
        return sid

    def __repr__(self) -> str:
        return (f"InsightBrowser(registry={self.registry_url}, "
                f"ahp_proxy={self.ahp_proxy_url}, "
                f"reliability={self.reliability_url})")


def _urlencode(s: str) -> str:
    """Simple URL encoding without external deps."""
    import urllib.parse
    return urllib.parse.quote(s, safe="")
