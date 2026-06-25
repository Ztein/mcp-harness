"""T011 — agent-loopen som testbar motor (``run_turn``).

Kör motorn mot en **riktig** fejk-LLM (HTTP) och en **riktig** fejk-MCP-session.
Motorn producerar strukturerade händelser (inte print-strängar) — fundamentet
för JSONL (T020), exit-kod (T022) och loop-broms (T023).
"""

from __future__ import annotations

import json
from contextlib import AbstractAsyncContextManager
from typing import Any

from mcp.client.session import ClientSession

from mcp_harness.engine import run_turn
from mcp_harness.events import AssistantText, ToolCall, ToolResult, TurnError
from mcp_harness.llm import chat_completion
from mcp_harness.tools import to_openai_tools
from tests.conftest import FakeLLM

Session = AbstractAsyncContextManager[ClientSession]


def real_llm(messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
    """LlmFn som verkligen anropar fejk-LLM över HTTP och plockar assistent-meddelandet."""
    message: dict[str, Any] = chat_completion(messages, tools)["choices"][0]["message"]
    return message


def tool_call_response(call_id: str, name: str, args: dict[str, Any]) -> dict[str, Any]:
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": call_id,
                            "type": "function",
                            "function": {"name": name, "arguments": json.dumps(args)},
                        }
                    ],
                }
            }
        ]
    }


def text_response(text: str) -> dict[str, Any]:
    return {"choices": [{"message": {"role": "assistant", "content": text}}]}


async def _tools(session: ClientSession) -> list[dict[str, Any]]:
    return to_openai_tools((await session.list_tools()).tools)


async def test_plain_text_turn(fake_llm: FakeLLM, connected_session: Session) -> None:
    fake_llm.queue(text_response("hej där"))
    async with connected_session as session:
        messages: list[dict[str, Any]] = [{"role": "user", "content": "hej"}]
        events = await run_turn(
            call_tool=session.call_tool,
            llm=real_llm,
            messages=messages,
            oai_tools=await _tools(session),
        )
    assert len(events) == 1
    assert isinstance(events[0], AssistantText)
    assert events[0].text == "hej där"


async def test_single_tool_call_then_text(fake_llm: FakeLLM, connected_session: Session) -> None:
    fake_llm.queue(tool_call_response("c1", "echo", {"text": "hej"}))
    fake_llm.queue(text_response("klart"))
    async with connected_session as session:
        messages: list[dict[str, Any]] = [{"role": "user", "content": "eka hej"}]
        events = await run_turn(
            call_tool=session.call_tool,
            llm=real_llm,
            messages=messages,
            oai_tools=await _tools(session),
        )
    assert [type(e).__name__ for e in events] == ["ToolCall", "ToolResult", "AssistantText"]
    tc, tr, at = events
    assert isinstance(tc, ToolCall) and tc.name == "echo" and tc.arguments == {"text": "hej"}
    assert isinstance(tr, ToolResult) and tr.text == "hej" and tr.is_error is False
    assert isinstance(at, AssistantText) and at.text == "klart"


async def test_chained_tool_calls(fake_llm: FakeLLM, connected_session: Session) -> None:
    fake_llm.queue(tool_call_response("c1", "echo", {"text": "a"}))
    fake_llm.queue(tool_call_response("c2", "echo", {"text": "b"}))
    fake_llm.queue(text_response("done"))
    async with connected_session as session:
        messages: list[dict[str, Any]] = [{"role": "user", "content": "två"}]
        events = await run_turn(
            call_tool=session.call_tool,
            llm=real_llm,
            messages=messages,
            oai_tools=await _tools(session),
        )
    assert [type(e).__name__ for e in events] == [
        "ToolCall",
        "ToolResult",
        "ToolCall",
        "ToolResult",
        "AssistantText",
    ]


async def test_tool_error_is_event_not_crash(fake_llm: FakeLLM, connected_session: Session) -> None:
    fake_llm.queue(tool_call_response("c1", "boom", {}))
    fake_llm.queue(text_response("hanterat"))
    async with connected_session as session:
        messages: list[dict[str, Any]] = [{"role": "user", "content": "spräng"}]
        events = await run_turn(
            call_tool=session.call_tool,
            llm=real_llm,
            messages=messages,
            oai_tools=await _tools(session),
        )
    tr = events[1]
    assert isinstance(tr, ToolResult) and tr.is_error is True
    assert "avsiktligt fel" in tr.text
    assert isinstance(events[-1], AssistantText)


async def test_full_args_preserved(fake_llm: FakeLLM, connected_session: Session) -> None:
    big = {"text": "x" * 1000, "nested": {"a": [1, 2, 3], "b": " åäö"}}
    fake_llm.queue(tool_call_response("c1", "echo", big))
    fake_llm.queue(text_response("ok"))
    async with connected_session as session:
        messages: list[dict[str, Any]] = [{"role": "user", "content": "stora args"}]
        events = await run_turn(
            call_tool=session.call_tool,
            llm=real_llm,
            messages=messages,
            oai_tools=await _tools(session),
        )
    tc = events[0]
    assert isinstance(tc, ToolCall)
    assert tc.arguments == big  # exakt, ingen förlust


async def test_llm_error_is_turn_error_not_crash(connected_session: Session) -> None:
    def boom_llm(messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
        raise RuntimeError("LLM nere")

    async with connected_session as session:
        messages: list[dict[str, Any]] = [{"role": "user", "content": "x"}]
        events = await run_turn(
            call_tool=session.call_tool, llm=boom_llm, messages=messages, oai_tools=[]
        )
    assert len(events) == 1
    assert isinstance(events[0], TurnError)
    assert "LLM nere" in events[0].message


async def test_tool_call_cap_trips(fake_llm: FakeLLM, connected_session: Session) -> None:
    # Modellen ber om verktyg i all oändlighet → taket bryter loopen högljutt.
    for i in range(10):
        fake_llm.queue(tool_call_response(f"c{i}", "echo", {"text": str(i)}))
    async with connected_session as session:
        messages: list[dict[str, Any]] = [{"role": "user", "content": "loopa"}]
        events = await run_turn(
            call_tool=session.call_tool,
            llm=real_llm,
            messages=messages,
            oai_tools=await _tools(session),
            max_tool_calls=3,
        )
    assert isinstance(events[-1], TurnError)
    assert sum(isinstance(e, ToolCall) for e in events) == 3
