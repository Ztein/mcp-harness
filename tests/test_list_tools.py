"""T025 — non-interaktiv verktygsdump (`--list-tools`).

Bannern ger *antal* verktyg och `/tools` finns interaktivt; en scriptad körning
behöver kunna fånga hela ytan (namn + beskrivning + parametrar) för att
versionsstämpla *vilken yta som testades*. Dumpen sker utan LLM-anrop och utan
tur — den rena renderingen testas direkt, hela vägen mot en riktig stdio-MCP.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from mcp.types import Tool

from mcp_harness.cli import dump_tool_surface
from mcp_harness.config import ServerConfig
from mcp_harness.tools import render_tool_surface, tool_surface

ROOT = Path(__file__).resolve().parents[1]


def make_tool(name: str, schema: dict[str, Any] | None = None, desc: str | None = None) -> Tool:
    return Tool(name=name, description=desc, inputSchema=schema or {"type": "object"})


def test_surface_has_name_description_parameters() -> None:
    tools = [
        make_tool("echo", {"type": "object", "properties": {"text": {"type": "string"}}}, "Eka"),
    ]
    surface = tool_surface(tools)
    assert surface == [
        {
            "name": "echo",
            "description": "Eka",
            "parameters": {"type": "object", "properties": {"text": {"type": "string"}}},
        }
    ]


def test_surface_sorted_by_name() -> None:
    surface = tool_surface([make_tool("zeta"), make_tool("alpha")])
    assert [e["name"] for e in surface] == ["alpha", "zeta"]


def test_render_json_is_parseable_one_entry_per_tool() -> None:
    out = render_tool_surface([make_tool("echo"), make_tool("boom")], as_json=True)
    parsed = json.loads(out)
    assert {e["name"] for e in parsed} == {"echo", "boom"}
    assert all({"name", "description", "parameters"} <= e.keys() for e in parsed)


def test_render_human_lists_names_and_params() -> None:
    out = render_tool_surface(
        [make_tool("echo", {"type": "object", "properties": {"text": {"type": "string"}}})],
        as_json=False,
    )
    assert "- echo" in out
    assert "text" in out


def test_render_respects_scoping() -> None:
    # apply_allowlist sker uppströms; dumpen renderar bara det den får.
    out = render_tool_surface([make_tool("echo")], as_json=True)
    assert "boom" not in out


async def test_dump_over_stdio_no_llm_needed() -> None:
    # Hela vägen mot en riktig stdio-MCP, utan att någon LLM_*-env är satt:
    # bevisar att dump-vägen aldrig rör LLM:en.
    server = ServerConfig(
        name="fake",
        transport="stdio",
        command=sys.executable,
        args=["-m", "tests.support.fake_mcp", "--stdio"],
        cwd=str(ROOT),
    )
    out = await dump_tool_surface([server], None, as_json=True)
    names = {e["name"] for e in json.loads(out)}
    assert {"echo", "multi_block", "boom", "structured"} <= names


async def test_dump_over_stdio_respects_allowlist() -> None:
    server = ServerConfig(
        name="fake",
        transport="stdio",
        command=sys.executable,
        args=["-m", "tests.support.fake_mcp", "--stdio"],
        cwd=str(ROOT),
    )
    out = await dump_tool_surface([server], {"echo"}, as_json=True)
    names = {e["name"] for e in json.loads(out)}
    assert names == {"echo"}
