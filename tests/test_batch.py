"""T023 — batch-resiliens: ett slutligt LLM-fel mitt i en batch får inte
korrumpera resten (PRD §11). Varje tur är oberoende; ett fel blir en händelse,
nästa tur körs ändå. Loop-bromsen (tak/tur) testas i test_engine.py.
"""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import Any

from mcp.client.session import ClientSession

from mcp_harness.engine import RunSummary, run_turn, tally_turn
from mcp_harness.events import AssistantText, TurnError

Session = AbstractAsyncContextManager[ClientSession]


class FlakyLlm:
    """En LlmFn som reser sig på det N:te anropet (simulerar ett slutligt fel
    mitt i en batch), annars ger ett textsvar."""

    def __init__(self, fail_on_call: int) -> None:
        self._n = 0
        self._fail_on = fail_on_call

    def __call__(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> dict[str, Any]:
        self._n += 1
        if self._n == self._fail_on:
            raise RuntimeError("slutligt LLM-fel")
        # LlmFn returnerar assistent-meddelandet (content, ev. tool_calls).
        return {"content": f"svar {self._n}"}


async def test_batch_continues_after_midstream_error(connected_session: Session) -> None:
    llm = FlakyLlm(fail_on_call=2)  # tur 2 failar
    summary = RunSummary()
    results = []
    async with connected_session as session:
        messages: list[dict[str, Any]] = [{"role": "system", "content": "s"}]
        for i in range(3):
            messages.append({"role": "user", "content": f"tur {i}"})
            events = await run_turn(session=session, llm=llm, messages=messages, oai_tools=[])
            tally_turn(summary, events)
            results.append(events)

    # Tur 1 och 3 lyckades; tur 2 är ett TurnError — men 3 kördes ändå.
    assert isinstance(results[0][-1], AssistantText)
    assert isinstance(results[1][-1], TurnError)
    assert isinstance(results[2][-1], AssistantText)
    assert summary.turns == 3
    assert summary.failed_turns == 1
    assert summary.exit_code == 1  # batch-fel sätter exit≠0
