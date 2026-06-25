"""T002 — tester för den in-process fejk-MCP-servern (fixturen ``connected_session``).

Kör mot en riktig ClientSession kopplad till en riktig MCP-server — inga mockar
av session/call_tool/list_tools. Detta är fundamentet som T010–T012 bygger på.
Varje test öppnar context-managern i sin egen task (anyio-krav).
"""

from __future__ import annotations

import json
from contextlib import AbstractAsyncContextManager

from mcp.client.session import ClientSession

from tests.conftest import texts_of

Session = AbstractAsyncContextManager[ClientSession]


async def test_fixture_lists_expected_tools(connected_session: Session) -> None:
    async with connected_session as session:
        names = {t.name for t in (await session.list_tools()).tools}
    assert {"echo", "multi_block", "boom", "structured"} <= names


async def test_echo_roundtrips(connected_session: Session) -> None:
    async with connected_session as session:
        result = await session.call_tool("echo", {"text": "hej"})
    assert texts_of(result) == ["hej"]


async def test_multi_block_returns_multiple_blocks(connected_session: Session) -> None:
    async with connected_session as session:
        result = await session.call_tool("multi_block", {})
    # Bevisar att fixturen kan reproducera T012: bara content[0] vore "block-A"
    # och tappade "block-B" tyst.
    assert texts_of(result) == ["block-A", "block-B"]
    assert len(result.content) > 1


async def test_boom_returns_error(connected_session: Session) -> None:
    async with connected_session as session:
        result = await session.call_tool("boom", {})
    assert result.isError is True
    assert "avsiktligt fel" in texts_of(result)[0]


async def test_structured_fields_accessible(connected_session: Session) -> None:
    async with connected_session as session:
        result = await session.call_tool("structured", {})
    # JSON-fält ska gå att läsa ut (PRD §11 fält-assertion) — via structuredContent
    # om det finns, annars genom att tolka textblocket som JSON.
    data = result.structuredContent or json.loads(texts_of(result)[0])
    assert data["id"] == "abc-123"
    assert data["missing"] == ["alpha", "beta"]
