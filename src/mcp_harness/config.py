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
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ServerConfig:
    name: str
    transport: str = "http"  # "http" | "stdio"
    # http
    url: str = ""
    key: str = ""
    # stdio (subprocess: command + args, pratar över stdin/stdout)
    command: str = ""
    args: list[str] = field(default_factory=list)
    env: dict[str, str] | None = None
    cwd: str | None = None


def _parse_entry(entry: object, where: str) -> ServerConfig:
    if not isinstance(entry, dict) or "name" not in entry:
        raise SystemExit(f"❌ {where}: varje server kräver minst 'name'.")
    name = str(entry["name"])
    transport = str(entry.get("transport", "http"))
    if transport == "stdio":
        if "command" not in entry:
            raise SystemExit(f"❌ {where}: stdio-server '{name}' kräver 'command'.")
        return ServerConfig(
            name=name,
            transport="stdio",
            command=str(entry["command"]),
            args=[str(a) for a in entry.get("args", [])],
            env={str(k): str(v) for k, v in (entry.get("env") or {}).items()} or None,
            cwd=str(entry["cwd"]) if entry.get("cwd") else None,
        )
    if transport == "http":
        if "url" not in entry:
            raise SystemExit(f"❌ {where}: http-server '{name}' kräver 'url'.")
        return ServerConfig(
            name=name, transport="http", url=str(entry["url"]), key=str(entry.get("key", ""))
        )
    raise SystemExit(f"❌ {where}: okänd transport '{transport}' för '{name}' (http|stdio).")


def load_servers(path: str | Path) -> list[ServerConfig]:
    """Läs en server-config. Failar hårt på trasig JSON, tom lista, saknade fält
    (per transport) eller dubbletter av server-namn."""
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
        cfg = _parse_entry(entry, str(p))
        if cfg.name in seen:
            raise SystemExit(f"❌ {p}: dubblett av server-namn '{cfg.name}'.")
        seen.add(cfg.name)
        out.append(cfg)
    return out
