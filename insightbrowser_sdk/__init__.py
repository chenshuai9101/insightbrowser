"""InsightBrowser SDK — Agent-to-Agent communication library.

Pure Python, zero external dependencies. Uses urllib for HTTP.

Usage:
    from insightbrowser_sdk import InsightBrowser

    ib = InsightBrowser(registry_url="http://localhost:7000")
    site = ib.discover("用户需求洞察")
    result = ib.call(site, {"action": "analyze", "data": {"texts": [...]}})
"""

from .client import InsightBrowser, DEFAULT_RELIABILITY_URL
from .models import Site, AgentManifest
from .errors import InsightBrowserError, SiteNotFoundError, ActionError

__all__ = [
    "InsightBrowser",
    "Site",
    "AgentManifest",
    "InsightBrowserError",
    "SiteNotFoundError",
    "ActionError",
    "DEFAULT_RELIABILITY_URL",
]
