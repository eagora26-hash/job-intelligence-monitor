"""MCP server configuration model + loader.

Loads MCP server definitions from a JSON file (default ``job_monitor/mcp/servers.json``) using
the familiar ``{"mcpServers": {name: {command, args, env, ...}}}`` shape used by MCP clients.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

_DEFAULT_CONFIG = Path(__file__).resolve().parent / "servers.json"


@dataclass
class MCPServerConfig:
    """A single MCP server definition."""

    name: str
    command: str = ""
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    transport: str = "stdio"  # "stdio" | "sse" | "http"
    url: str = ""
    enabled: bool = True
    description: str = ""

    @classmethod
    def from_dict(cls, name: str, data: Dict) -> "MCPServerConfig":
        return cls(
            name=name,
            command=data.get("command", ""),
            args=list(data.get("args", [])),
            env=dict(data.get("env", {})),
            transport=data.get("transport", "stdio"),
            url=data.get("url", ""),
            enabled=data.get("enabled", True),
            description=data.get("description", ""),
        )


def load_mcp_config(path: Optional[Path | str] = None) -> List[MCPServerConfig]:
    """Load MCP server configs from ``path`` (or the bundled default). Empty list if missing."""
    config_path = Path(path) if path else _DEFAULT_CONFIG
    if not config_path.exists():
        return []
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    servers = raw.get("mcpServers", {})
    return [MCPServerConfig.from_dict(name, data) for name, data in servers.items()]
