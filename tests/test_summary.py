"""T022 — körnings-sammanfattning och exit-kod.

En körning ska kunna greenas/rödas programmatiskt (PRD §11): exit≠0 om en tur
slutligen misslyckades. En tur räknas som misslyckad endast om dess **sista**
händelse är ett ``TurnError`` — ett verktygsfel som modellen sedan hanterar är
inte en misslyckad tur.
"""

from __future__ import annotations

from mcp_harness.engine import RunSummary, tally_turn
from mcp_harness.events import AssistantText, ToolCall, ToolResult, TurnError


def test_summary_counts_turns_and_calls() -> None:
    s = RunSummary()
    tally_turn(
        s,
        [
            ToolCall(name="echo", arguments={}, call_id="c1"),
            ToolResult(call_id="c1", name="echo", text="x"),
            AssistantText(text="ok"),
        ],
    )
    tally_turn(s, [AssistantText(text="hej")])
    assert s.turns == 2
    assert s.tool_calls == 1
    assert s.failed_turns == 0
    assert s.exit_code == 0


def test_summary_counts_failed_turn() -> None:
    s = RunSummary()
    tally_turn(s, [TurnError(message="LLM nere")])
    assert s.failed_turns == 1
    assert s.exit_code == 1


def test_tool_error_is_not_a_failed_turn() -> None:
    # Verktygsfel mitt i, men textsvar sist → lyckad tur (skiljt från turfel).
    s = RunSummary()
    tally_turn(
        s,
        [
            ToolCall(name="boom", arguments={}, call_id="c1"),
            ToolResult(call_id="c1", name="boom", text="fel", is_error=True),
            AssistantText(text="hanterat"),
        ],
    )
    assert s.failed_turns == 0
    assert s.exit_code == 0
