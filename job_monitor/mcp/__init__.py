"""Model Context Protocol (MCP) support.

Provides a configuration loader, a server registry, and a plugin-hook interface so the monitor
can be exposed to / extended by MCP-compatible agent tooling. These are real abstractions —
config management + registration — not fake server implementations.
"""

from job_monitor.mcp.config import MCPServerConfig, load_mcp_config
from job_monitor.mcp.registry import MCPPlugin, MCPServerRegistry

__all__ = ["MCPServerConfig", "load_mcp_config", "MCPServerRegistry", "MCPPlugin"]
