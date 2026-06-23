"""
Channel Registry - Multi-backend routing for external services.
Each channel = one external platform/service, with backend priority list.
Inspired by Agent-Reach's channels/ architecture.

Usage:
    from channels import registry
    status = registry.detect_all()  # returns {channel_name: status}
"""

import importlib
import pkgutil
from typing import List, Optional, Callable


class Backend:
    """A single backend implementation for a channel."""
    
    def __init__(self, name: str, description: str, detect_fn: Optional[Callable] = None):
        self.name = name
        self.description = description
        self.detect_fn = detect_fn or (lambda: {"status": "unknown"})
    
    def detect(self) -> dict:
        """Detect if this backend is available."""
        try:
            return self.detect_fn()
        except Exception as e:
            return {"status": "error", "error": str(e)}


class Channel:
    """A capability channel with multi-backend routing."""
    
    def __init__(self, name: str, description: str, backends: List[Backend], icon: str = "🔌"):
        self.name = name
        self.description = description
        self.backends = backends  # Ordered list: preferred first
        self.icon = icon
        self._active_backend = None
        self._last_detect = None
    
    def detect(self) -> dict:
        """Detect all backends and return status. Auto-selects best available."""
        results = []
        active = None
        
        for backend in self.backends:
            result = backend.detect()
            result["backend"] = backend.name
            results.append(result)
            if result.get("status") == "online" and not active:
                active = backend.name
        
        self._active_backend = active
        self._last_detect = {
            "channel": self.name,
            "status": "online" if active else "offline",
            "active_backend": active or "none",
            "backends": results,
        }
        return self._last_detect


class ChannelRegistry:
    """Registry of all capability channels."""
    
    def __init__(self):
        self._channels: dict[str, Channel] = {}
    
    def register(self, channel: Channel):
        self._channels[channel.name] = channel
    
    def get(self, name: str) -> Optional[Channel]:
        return self._channels.get(name)
    
    def list(self) -> list:
        return list(self._channels.values())
    
    def detect_all(self) -> dict:
        """Detect status of all channels. Returns dict keyed by channel name."""
        results = {}
        for name, channel in self._channels.items():
            results[name] = channel.detect()
        return results
    
    def get_health_summary(self) -> dict:
        """Get overall channel health summary for doctor API."""
        all_results = self.detect_all()
        online = sum(1 for r in all_results.values() if r.get("status") == "online")
        offline = sum(1 for r in all_results.values() if r.get("status") == "offline")
        return {
            "channels": all_results,
            "summary": {
                "total": len(all_results),
                "online": online,
                "offline": offline,
            }
        }


# Global registry instance
registry = ChannelRegistry()


def auto_discover():
    """Auto-discover and register all channel modules in this package."""
    import channels as pkg
    for importer, modname, ispkg in pkgutil.iter_modules(pkg.__path__):
        if modname == "__init__" or ispkg:
            continue
        try:
            mod = importlib.import_module(f"channels.{modname}")
            if hasattr(mod, "register"):
                mod.register(registry)
        except Exception as e:
            print(f"  ⚠️  Channel {modname} failed to register: {e}")


# Auto-discover on import
auto_discover()
