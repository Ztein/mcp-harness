"""Config för flera MCP-servrar (T030, PRD §6.2).

Config är data, inte kod (princip 1). En liten JSON-fil listar namngivna servrar
(likt Claude Desktops ``mcpServers``). Trasig/ofullständig config failar hårt
(princip 3).

    {"servers": [
      {"name": "ado", "url": "http://host/mcp", "key": "..."},
      {"name": "intric", "url": "http://other/mcp", "key": "..."}
    ]}
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ServerConfig:
    name: str
    url: str
    key: str = ""


def load_servers(path: str | Path) -> list[ServerConfig]:
    """Läs en server-config. Failar hårt på trasig JSON, tom lista, saknade fält
    eller dubbletter av server-namn."""
    p = Path(path)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"❌ {p}: ogiltig JSON: {exc}") from exc

    servers = data.get("servers") if isinstance(data, dict) else None
    if not isinstance(servers, list) or not servers:
        raise SystemExit(f"❌ {p}: kräver en icke-tom 'servers'-lista.")

    out: list[ServerConfig] = []
    seen: set[str] = set()
    for entry in servers:
        if not isinstance(entry, dict) or "name" not in entry or "url" not in entry:
            raise SystemExit(f"❌ {p}: varje server kräver minst 'name' och 'url'.")
        name = str(entry["name"])
        if name in seen:
            raise SystemExit(f"❌ {p}: dubblett av server-namn '{name}'.")
        seen.add(name)
        out.append(ServerConfig(name=name, url=str(entry["url"]), key=str(entry.get("key", ""))))
    return out
