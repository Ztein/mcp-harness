"""T010 — rena funktioner: MCP-verktyg → OpenAI-schema, och allowlist-filtrering.

Menyn modellen ser måste exakt spegla allowlisten (PRD §11). Okänt verktyg i
allowlisten failar hårt. Konstruerar riktiga ``mcp.types.Tool`` (inte mockar) och
verifierar dessutom mot fejk-MCP-serverns faktiska verktyg.
"""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import Any

import pytest
from mcp.client.session import ClientSession
from mcp.types import Tool

from mcp_harness.tools import apply_allowlist, to_openai_tools

Session = AbstractAsyncContextManager[ClientSession]


def make_tool(
    name: str, description: str | None = None, schema: dict[str, Any] | None = None
) -> Tool:
    return Tool(
        name=name,
        description=description,
        inputSchema=schema or {"type": "object", "properties": {}},
    )


def test_to_openai_tools_maps_fields() -> None:
    schema = {"type": "object", "properties": {"text": {"type": "string"}}}
    out = to_openai_tools([make_tool("echo", "Eka tillbaka", schema)])
    fn = out[0]["function"]
    assert out[0]["type"] == "function"
    assert fn["name"] == "echo"
    assert fn["description"] == "Eka tillbaka"
    # inputSchema bevaras oförändrat — kontraktet mot modellen.
    assert fn["parameters"] == schema


def test_to_openai_tools_empty_description() -> None:
    out = to_openai_tools([make_tool("x", None)])
    assert out[0]["function"]["description"] == ""


def test_allowlist_filters_subset() -> None:
    tools = [make_tool("echo"), make_tool("boom")]
    assert [t.name for t in apply_allowlist(tools, {"echo"})] == ["echo"]


def test_allowlist_unknown_fails_loudly() -> None:
    with pytest.raises(SystemExit) as exc:
        apply_allowlist([make_tool("echo")], {"finns_ej"})
    msg = str(exc.value)
    # Både det okända och de tillgängliga ska nämnas.
    assert "finns_ej" in msg
    assert "echo" in msg


def test_allowlist_none_returns_all() -> None:
    tools = [make_tool("a"), make_tool("b")]
    assert len(apply_allowlist(tools, None)) == 2


async def test_to_openai_tools_from_real_session(connected_session: Session) -> None:
    async with connected_session as session:
        tools = (await session.list_tools()).tools
    out = to_openai_tools(tools)
    names = {o["function"]["name"] for o in out}
    assert {"echo", "multi_block", "boom", "structured"} <= names
    assert all(o["function"]["parameters"] is not None for o in out)
