"""T001 — tester för den provider-agnostiska LLM-klienten.

Kör mot ``fake_llm`` (en riktig HTTP-server), inte mot mockar — så
request-bygge, headers, retry och JSON-parse exekveras på riktigt.
"""

from __future__ import annotations

import pytest

from mcp_harness.llm import chat_completion, llm_model
from tests.conftest import FakeLLM


def test_chat_completion_returns_full_response(fake_llm: FakeLLM) -> None:
    fake_llm.queue(
        {
            "choices": [{"message": {"content": "hej"}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 1},
        }
    )
    result = chat_completion([{"role": "user", "content": "hej"}])
    # HELA svaret returneras, inkl. usage (det T020 senare loggar).
    assert result["choices"][0]["message"]["content"] == "hej"
    assert result["usage"]["prompt_tokens"] == 3


def test_chat_completion_sends_bearer_and_model(fake_llm: FakeLLM) -> None:
    fake_llm.queue({"choices": [{"message": {"content": "ok"}}]})
    chat_completion([{"role": "user", "content": "x"}])
    req = fake_llm.requests[-1]
    assert req["headers"].get("Authorization") == "Bearer test-key"
    assert req["body"]["model"] == "test-model"
    assert req["body"]["messages"] == [{"role": "user", "content": "x"}]


def test_tools_set_tool_choice_auto(fake_llm: FakeLLM) -> None:
    fake_llm.queue({"choices": [{"message": {"content": "ok"}}]})
    tools = [{"type": "function", "function": {"name": "echo", "parameters": {}}}]
    chat_completion([{"role": "user", "content": "x"}], tools)
    body = fake_llm.requests[-1]["body"]
    assert body["tools"] == tools
    assert body["tool_choice"] == "auto"


def test_no_tools_omits_tool_keys(fake_llm: FakeLLM) -> None:
    fake_llm.queue({"choices": [{"message": {"content": "ok"}}]})
    chat_completion([{"role": "user", "content": "x"}])
    body = fake_llm.requests[-1]["body"]
    assert "tools" not in body
    assert "tool_choice" not in body


def test_require_missing_env_exits_loudly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_MODEL", raising=False)
    with pytest.raises(SystemExit) as exc:
        llm_model()
    assert "LLM_MODEL" in str(exc.value)


def test_retry_then_success(fake_llm: FakeLLM, monkeypatch: pytest.MonkeyPatch) -> None:
    # Hoppa över den riktiga backoff-sömnen så testet är snabbt.
    monkeypatch.setattr("mcp_harness.llm.time.sleep", lambda _s: None)
    fake_llm.queue_status(503, times=2)
    fake_llm.queue({"choices": [{"message": {"content": "till slut"}}]})
    result = chat_completion([{"role": "user", "content": "x"}], max_retries=3)
    assert result["choices"][0]["message"]["content"] == "till slut"
    assert len(fake_llm.requests) == 3  # två fel + ett lyckat — alla syntes


def test_retry_exhausted_raises(fake_llm: FakeLLM, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("mcp_harness.llm.time.sleep", lambda _s: None)
    fake_llm.queue_status(503, times=5)
    # Sista felet propageras (sväljs aldrig tyst) — princip 3.
    with pytest.raises(Exception):  # noqa: B017 (URLError/HTTPError — vi bryr oss om att det reser sig)
        chat_completion([{"role": "user", "content": "x"}], max_retries=3)
