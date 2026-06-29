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


def _turn_with_tool_error() -> list[object]:
    return [
        ToolCall(name="boom", arguments={}, call_id="c1"),
        ToolResult(call_id="c1", name="boom", text="fel", is_error=True),
        AssistantText(text="hanterat"),
    ]


def test_tool_error_counted_in_summary() -> None:
    # F3: tool-fel ska aggregeras och synas — även om turen i övrigt lyckades.
    s = RunSummary()
    tally_turn(s, _turn_with_tool_error())
    assert s.tool_errors == 1
    assert "1 verktygsfel" in s.line()


def test_tool_error_does_not_gate_by_default() -> None:
    # Default: ett hanterat tool-fel grindar inte körningen rött (bakåtkompat).
    s = RunSummary()
    tally_turn(s, _turn_with_tool_error())
    assert s.exit_code == 0


def test_fail_on_tool_error_flag_gates() -> None:
    # Med opt-in-policyn blir exit ≠0 vid ≥1 tool-fel.
    s = RunSummary(fail_on_tool_error=True)
    tally_turn(s, _turn_with_tool_error())
    assert s.tool_errors == 1
    assert s.exit_code == 1


def test_summary_and_exit_consistent_no_phantom_gate() -> None:
    # Ingen "exit 0 + grindat fel": utan tool-fel grindar flaggan ingenting.
    s = RunSummary(fail_on_tool_error=True)
    tally_turn(s, [AssistantText(text="ok")])
    assert s.tool_errors == 0
    assert s.exit_code == 0
