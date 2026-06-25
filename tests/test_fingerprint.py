"""T021 — server-fingeravtryck + `--expect-tools` (fail-hard mot stale server).

En stale server (rätt antal verktyg, gammal kod) ska inte kunna maskera sig
(PRD §11). Fingeravtrycket är stabilt för samma schema och ändras när ett verktygs
schema ändras; `--expect-tools` failar högljutt vid avvikelse.
"""

from __future__ import annotations

from typing import Any

import pytest
from mcp.types import Tool

from mcp_harness.tools import apply_allowlist, check_expected_tools, tools_fingerprint


def make_tool(name: str, schema: dict[str, Any] | None = None) -> Tool:
    return Tool(name=name, description=None, inputSchema=schema or {"type": "object"})


def test_fingerprint_stable_across_runs() -> None:
    tools = [make_tool("echo"), make_tool("boom")]
    assert tools_fingerprint(tools) == tools_fingerprint(tools)


def test_fingerprint_order_independent() -> None:
    a = [make_tool("echo"), make_tool("boom")]
    b = [make_tool("boom"), make_tool("echo")]
    assert tools_fingerprint(a) == tools_fingerprint(b)


def test_fingerprint_changes_on_schema_change() -> None:
    before = [make_tool("echo", {"type": "object", "properties": {}})]
    after = [make_tool("echo", {"type": "object", "properties": {"text": {"type": "string"}}})]
    assert tools_fingerprint(before) != tools_fingerprint(after)


def test_fingerprint_reflects_allowlist() -> None:
    tools = [make_tool("echo"), make_tool("boom")]
    full = tools_fingerprint(tools)
    scoped = tools_fingerprint(apply_allowlist(tools, {"echo"}))
    assert full != scoped


def test_expect_tools_match_passes() -> None:
    tools = [make_tool("echo"), make_tool("boom")]
    check_expected_tools(tools, {"echo", "boom"})  # ska inte resa sig


def test_expect_tools_missing_fails_loudly() -> None:
    tools = [make_tool("echo")]
    with pytest.raises(SystemExit) as exc:
        check_expected_tools(tools, {"echo", "saknas"})
    assert "saknas" in str(exc.value)


def test_expect_tools_unexpected_fails_loudly() -> None:
    tools = [make_tool("echo"), make_tool("extra")]
    with pytest.raises(SystemExit) as exc:
        check_expected_tools(tools, {"echo"})
    assert "extra" in str(exc.value)
