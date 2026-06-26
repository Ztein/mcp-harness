"""T034 — stdio-transport: starta fejk-MCP som subprocess och anslut på riktigt.

Som CLI:t gör mot en riktig stdio-MCP (command + args, stdin/stdout). Ingen mock —
en faktisk subprocess och en riktig ClientSession.
"""

from __future__ import annotations

import sys
from pathlib import Path

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from tests.conftest import texts_of

ROOT = Path(__file__).resolve().parents[1]


async def test_stdio_lists_tools_over_subprocess() -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "tests.support.fake_mcp", "--stdio"],
        cwd=str(ROOT),
    )
    async with stdio_client(params) as (r, w), ClientSession(r, w) as session:
        await session.initialize()
        names = {t.name for t in (await session.list_tools()).tools}
        result = await session.call_tool("echo", {"text": "hej"})
    assert {"echo", "multi_block", "boom", "structured"} <= names
    assert texts_of(result) == ["hej"]
