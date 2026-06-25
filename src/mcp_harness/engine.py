"""Agent-loopen som en testbar motor (T011).

``run_turn`` kör en tur: anropa modellen → kör de verktyg den ber om → mata
tillbaka svaren → upprepa tills ett textsvar. Den är fri från ``input()``/
``print()`` (I/O bor i CLI:t) och tar sina beroenden injicerade (en ``LlmFn`` och
en ``ClientSession``), så hela loopen kan testas mot en riktig fejk-LLM + fejk-MCP.

``extract_tool_result`` (T012) ger **full verktygssvars-trohet**: alla text-block
konkateneras, icke-text-block representeras i stället för att tappas tyst, och
strukturerat innehåll bevaras.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from mcp.types import CallToolResult, TextContent

from .events import AssistantText, Event, ToolCall, ToolResult, TurnError

# En LlmFn tar (messages, tools) och returnerar assistent-meddelandet (med ev.
# tool_calls). Synkron — motorn bryr sig inte om hur anropet görs.
LlmFn = Callable[[list[dict[str, Any]], list[dict[str, Any]]], dict[str, Any]]

# En ToolCaller kör ett verktyg och ger dess råa resultat. För en server är det
# ``session.call_tool``; för flera (T030) en router som väljer rätt session.
ToolCaller = Callable[[str, dict[str, Any]], Awaitable[CallToolResult]]

DEFAULT_MAX_TOOL_CALLS = 50


@dataclass
class RunSummary:
    """Aggregerat utfall över en körning — gör den green/röd programmatiskt (T022)."""

    turns: int = 0
    tool_calls: int = 0
    failed_turns: int = 0

    @property
    def exit_code(self) -> int:
        """0 om alla turer lyckades, annars 1 (PRD §11)."""
        return 1 if self.failed_turns else 0

    def line(self) -> str:
        return (
            f"Sammanfattning: {self.turns} turer, {self.tool_calls} verktygsanrop, "
            f"{self.failed_turns} misslyckade turer."
        )


def tally_turn(summary: RunSummary, events: list[Event]) -> None:
    """Räkna in en turs händelser. En tur är misslyckad endast om dess sista
    händelse är ett ``TurnError`` (ett hanterat verktygsfel räknas inte)."""
    summary.turns += 1
    summary.tool_calls += sum(isinstance(e, ToolCall) for e in events)
    if events and isinstance(events[-1], TurnError):
        summary.failed_turns += 1


def extract_tool_result(name: str, call_id: str, result: CallToolResult) -> ToolResult:
    """Bygg en :class:`ToolResult` med full trohet (T012).

    - Konkatenera text ur **alla** ``TextContent``-block (inte bara ``content[0]``).
    - Representera icke-text-block (bild/resurs) med en not — tappa dem aldrig tyst.
    - Bevara ``structuredContent`` så fält kan assert:as (PRD §11).
    """
    texts = [b.text for b in result.content if isinstance(b, TextContent)]
    non_text = [b for b in result.content if not isinstance(b, TextContent)]
    body = "\n".join(texts) if texts else "(tomt)"
    if non_text:
        kinds = ", ".join(sorted({b.type for b in non_text}))
        note = f"[{len(non_text)} icke-text-block: {kinds}]"
        body = f"{body}\n{note}" if texts else note
    return ToolResult(
        call_id=call_id,
        name=name,
        text=body,
        is_error=bool(result.isError),
        block_count=len(result.content),
        non_text_blocks=len(non_text),
        structured=result.structuredContent,
    )


async def run_turn(
    *,
    call_tool: ToolCaller,
    llm: LlmFn,
    messages: list[dict[str, Any]],
    oai_tools: list[dict[str, Any]],
    max_tool_calls: int = DEFAULT_MAX_TOOL_CALLS,
) -> list[Event]:
    """Kör en tur till slut och returnera dess händelser.

    ``messages`` muteras (assistent-/verktygs-meddelanden läggs till) så samma
    lista kan bäras vidare till nästa tur. Ett LLM-fel eller verktygsfel blir en
    händelse — aldrig en krasch (batch-resiliens, princip 3). Taket på
    verktygsanrop är en backstop mot loopande modeller (T023 kopplar CLI-flaggan).
    """
    events: list[Event] = []
    tool_calls_made = 0
    while True:
        try:
            message = llm(messages, oai_tools)
        except Exception as exc:  # transient LLM-fel blir en händelse, inte krasch
            events.append(TurnError(message=f"LLM-anrop misslyckades: {exc}"))
            return events

        tool_calls = message.get("tool_calls")
        if not tool_calls:
            content = message.get("content") or "(tomt svar)"
            events.append(AssistantText(text=content))
            messages.append({"role": "assistant", "content": message.get("content")})
            return events

        messages.append(
            {"role": "assistant", "content": message.get("content"), "tool_calls": tool_calls}
        )
        for tc in tool_calls:
            name = tc["function"]["name"]
            args = json.loads(tc["function"].get("arguments") or "{}")
            call_id = tc["id"]
            events.append(ToolCall(name=name, arguments=args, call_id=call_id))
            try:
                result = await call_tool(name, args)
                tr = extract_tool_result(name, call_id, result)
            except Exception as exc:
                tr = ToolResult(
                    call_id=call_id, name=name, text=f"FEL vid verktygsanrop: {exc}", is_error=True
                )
            events.append(tr)
            messages.append({"role": "tool", "tool_call_id": call_id, "content": tr.text})
            tool_calls_made += 1
            if tool_calls_made >= max_tool_calls:
                events.append(
                    TurnError(message=f"tak nått: {max_tool_calls} verktygsanrop på en tur")
                )
                return events
