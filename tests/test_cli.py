"""T015 — CLI:ns stdout-vy markerar verktygsfel (samma distinktion som transkriptet)."""

from __future__ import annotations

import pytest

from mcp_harness.cli import _print_event
from mcp_harness.events import ToolResult


def test_print_event_marks_tool_error(capsys: pytest.CaptureFixture[str]) -> None:
    _print_event(ToolResult(call_id="c1", name="boom", text="trasig", is_error=True))
    out = capsys.readouterr().out
    assert "⚠️" in out
    assert "trasig" in out


def test_print_event_silent_on_ok_result(capsys: pytest.CaptureFixture[str]) -> None:
    # Lyckade verktygssvar går till transkriptet, inte stdout — oförändrat.
    _print_event(ToolResult(call_id="c1", name="echo", text="bra", is_error=False))
    assert capsys.readouterr().out == ""
