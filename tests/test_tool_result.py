"""T012 — full verktygssvars-trohet: ``extract_tool_result``.

Reproducerar och fixar buggen där bara ``content[0]`` lästes: alla text-block ska
konkateneras, icke-text-block får inte tappas tyst, struktur bevaras (PRD §11).
Konstruerar riktiga ``CallToolResult`` och kör även mot fejk-MCP-serverns
``multi_block`` för end-to-end-bevis.
"""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import Any

from mcp.client.session import ClientSession
from mcp.types import CallToolResult, ImageContent, TextContent

from mcp_harness.engine import extract_tool_result

Session = AbstractAsyncContextManager[ClientSession]


def ctr(
    blocks: list[Any], is_error: bool = False, structured: dict[str, Any] | None = None
) -> CallToolResult:
    return CallToolResult(content=blocks, isError=is_error, structuredContent=structured)


def test_multi_block_concatenated() -> None:
    r = ctr([TextContent(type="text", text="A"), TextContent(type="text", text="B")])
    tr = extract_tool_result("multi", "c1", r)
    # Båda blocken med, i ordning — content[0]-buggen vore bara "A".
    assert tr.text == "A\nB"
    assert tr.block_count == 2


def test_single_block_unchanged() -> None:
    tr = extract_tool_result("echo", "c1", ctr([TextContent(type="text", text="hej")]))
    assert tr.text == "hej"
    assert tr.is_error is False


def test_empty_content_safe() -> None:
    tr = extract_tool_result("x", "c1", ctr([]))
    assert tr.text == "(tomt)"  # explicit markör, ingen IndexError
    assert tr.block_count == 0


def test_non_text_block_not_dropped() -> None:
    r = ctr(
        [
            TextContent(type="text", text="bild:"),
            ImageContent(type="image", data="abc", mimeType="image/png"),
        ]
    )
    tr = extract_tool_result("x", "c1", r)
    assert "bild:" in tr.text
    assert tr.non_text_blocks == 1
    # Icke-text-blocket representeras, tappas inte tyst.
    assert "icke-text" in tr.text


def test_error_flag_preserved() -> None:
    tr = extract_tool_result(
        "boom", "c1", ctr([TextContent(type="text", text="fel")], is_error=True)
    )
    assert tr.is_error is True


def test_structured_preserved() -> None:
    r = ctr(
        [TextContent(type="text", text='{"id":"42"}')],
        structured={"id": "42", "missing": ["a"]},
    )
    tr = extract_tool_result("x", "c1", r)
    assert tr.structured == {"id": "42", "missing": ["a"]}


async def test_multi_block_via_real_session(connected_session: Session) -> None:
    async with connected_session as session:
        result = await session.call_tool("multi_block", {})
    tr = extract_tool_result("multi_block", "c1", result)
    assert tr.text == "block-A\nblock-B"
    assert tr.block_count == 2
