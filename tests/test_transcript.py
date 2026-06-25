"""T013 — människo-transkriptet som sink för motorns händelser.

``render_event`` är ren och testbar utan att starta en körning. Det stabila,
parsbara ``⚙ namn(args-json)``-formatet bevaras (PRD §11 P2). Trunkering med
``…`` sker **endast** i denna människo-vy — aldrig i datat (det är JSONL, T020).
"""

from __future__ import annotations

from mcp_harness.events import AssistantText, ToolCall, ToolResult, TurnError, UserTurn
from mcp_harness.transcript import render_event


def test_transcript_renders_tool_call_format() -> None:
    out = render_event(ToolCall(name="echo", arguments={"text": "hej"}, call_id="c1"))
    # Tecken-för-tecken-stabilt format som äldre parsers kan förlita sig på.
    assert '⚙ `echo({"text": "hej"})`' in out


def test_transcript_truncates_long_result_with_ellipsis() -> None:
    long = "x" * 1000
    out = render_event(ToolResult(call_id="c1", name="echo", text=long), truncate=500)
    assert "…" in out
    assert long not in out  # hela råa svaret syns inte i människo-vyn
    assert out.count("x") == 500  # exakt vy-gränsen


def test_transcript_short_result_not_truncated() -> None:
    out = render_event(ToolResult(call_id="c1", name="echo", text="kort"), truncate=500)
    assert "kort" in out
    assert "…" not in out


def test_transcript_marks_tool_error() -> None:
    # T015: ett verktygsfel ska SE UT som ett fel (princip 3), inte som ett
    # lyckat svar med samma →-prefix.
    err = render_event(ToolResult(call_id="c1", name="boom", text="trasig", is_error=True))
    ok = render_event(ToolResult(call_id="c1", name="echo", text="bra", is_error=False))
    assert "⚠️" in err
    assert "trasig" in err
    assert "⚠️" not in ok


def test_transcript_user_and_assistant_roles() -> None:
    assert "👤" in render_event(UserTurn(text="hej"))
    assert "🤖" in render_event(AssistantText(text="svar"))


def test_transcript_error_rendered() -> None:
    out = render_event(TurnError(message="nere"))
    assert "⚠️" in out
    assert "nere" in out
