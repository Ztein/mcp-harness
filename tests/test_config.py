"""T030 — config-fil med flera MCP-servrar, och verktygs-aggregering.

Config är data (princip 1). Trasig config failar hårt (princip 3). Namn-krockar
mellan servrar hanteras synligt — aldrig tyst överskuggning (PRD §6.2).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from mcp.types import Tool

from mcp_harness.config import ServerConfig, load_servers
from mcp_harness.tools import aggregate_tools


def _tool(name: str) -> Tool:
    return Tool(name=name, description=None, inputSchema={"type": "object"})


def test_load_servers_parses(tmp_path: Path) -> None:
    p = tmp_path / "servers.json"
    p.write_text(
        '{"servers":[{"name":"a","url":"http://a/mcp","key":"k1"},'
        '{"name":"b","url":"http://b/mcp"}]}',
        encoding="utf-8",
    )
    servers = load_servers(p)
    assert servers == [
        ServerConfig(name="a", url="http://a/mcp", key="k1"),
        ServerConfig(name="b", url="http://b/mcp", key=""),
    ]


def test_load_servers_broken_json_fails_loudly(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text("{inte json", encoding="utf-8")
    with pytest.raises(SystemExit):
        load_servers(p)


def test_load_servers_empty_fails_loudly(tmp_path: Path) -> None:
    p = tmp_path / "empty.json"
    p.write_text('{"servers":[]}', encoding="utf-8")
    with pytest.raises(SystemExit):
        load_servers(p)


def test_load_servers_duplicate_name_fails_loudly(tmp_path: Path) -> None:
    p = tmp_path / "dup.json"
    p.write_text(
        '{"servers":[{"name":"a","url":"http://a"},{"name":"a","url":"http://b"}]}',
        encoding="utf-8",
    )
    with pytest.raises(SystemExit):
        load_servers(p)


def test_aggregate_tools_combines_menus() -> None:
    tools, owner = aggregate_tools(
        [("a", [_tool("echo"), _tool("ping")]), ("b", [_tool("status")])]
    )
    assert {t.name for t in tools} == {"echo", "ping", "status"}
    assert owner == {"echo": "a", "ping": "a", "status": "b"}


def test_aggregate_tools_name_collision_fails_loudly() -> None:
    with pytest.raises(SystemExit) as exc:
        aggregate_tools([("a", [_tool("echo")]), ("b", [_tool("echo")])])
    msg = str(exc.value)
    assert "echo" in msg and "a" in msg and "b" in msg
