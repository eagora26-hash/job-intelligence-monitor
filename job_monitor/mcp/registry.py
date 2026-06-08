"""MCP server registry + plugin-hook interface.

The registry tracks configured MCP servers and lets the application expose its own capabilities
to agent tooling via lightweight :class:`MCPPlugin` hooks (e.g. "search_jobs", "get_analytics").
Designed for extensibility; no fake server processes are spawned.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from job_monitor.mcp.config import MCPServerConfig, load_mcp_config
from job_monitor.observability import get_logger

logger = get_logger("mcp.registry")


class MCPPlugin(ABC):
    """A capability the monitor can advertise to MCP-compatible clients."""

    name: str = "plugin"
    description: str = ""

    @abstractmethod
    def invoke(self, **kwargs) -> object:
        """Execute the plugin's capability and return a JSON-serializable result."""


class MCPServerRegistry:
    """Registers MCP server configs and local plugins."""

    def __init__(self) -> None:
        self._servers: Dict[str, MCPServerConfig] = {}
        self._plugins: Dict[str, MCPPlugin] = {}

    # -- servers --
    def register_server(self, config: MCPServerConfig) -> None:
        self._servers[config.name] = config
        logger.info("Registered MCP server '%s' (%s)", config.name, config.transport)

    def load_from_config(self, path: Optional[str] = None) -> int:
        configs = load_mcp_config(path)
        for config in configs:
            self.register_server(config)
        return len(configs)

    def server(self, name: str) -> Optional[MCPServerConfig]:
        return self._servers.get(name)

    def servers(self, *, enabled_only: bool = False) -> List[MCPServerConfig]:
        values = list(self._servers.values())
        return [s for s in values if s.enabled] if enabled_only else values

    # -- plugins --
    def register_plugin(self, plugin: MCPPlugin) -> None:
        self._plugins[plugin.name] = plugin
        logger.info("Registered MCP plugin '%s'", plugin.name)

    def plugin(self, name: str) -> Optional[MCPPlugin]:
        return self._plugins.get(name)

    def plugins(self) -> List[MCPPlugin]:
        return list(self._plugins.values())

    def manifest(self) -> Dict[str, object]:
        """A description of registered servers + plugins (for discovery / docs)."""
        return {
            "servers": [
                {"name": s.name, "transport": s.transport, "enabled": s.enabled,
                 "description": s.description}
                for s in self._servers.values()
            ],
            "plugins": [
                {"name": p.name, "description": p.description} for p in self._plugins.values()
            ],
        }
