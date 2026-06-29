"""T026 — typmedvetna LLM-fel + fail-fast på icke-transienta fel (F5).

Kör mot ``fake_llm`` (riktig HTTP) som de övriga LLM-testerna. Auth-fel (4xx)
ska faila direkt utan retry; timeout/5xx/connection retras och failar med en
typspecifik, handlingsbar rad. ``run_turn`` ska bära det kurerade meddelandet
verbatim i ``TurnError``.
"""

from __future__ import annotations

from typing import Any

import pytest

from mcp_harness.llm import LlmError, _final_message, chat_completion
from tests.conftest import FakeLLM


def test_auth_4xx_fails_fast_no_retry(
    fake_llm: FakeLLM, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("mcp_harness.llm.time.sleep", lambda _s: None)
    fake_llm.queue_status(401, times=5)  # gott om fel köade...
    with pytest.raises(LlmError):
        chat_completion([{"role": "user", "content": "x"}], max_retries=3)
    # ...men auth-fel retras inte: exakt ETT request gjordes.
    assert len(fake_llm.requests) == 1


def test_auth_message_actionable(fake_llm: FakeLLM) -> None:
    fake_llm.queue_status(401)
    with pytest.raises(LlmError) as exc:
        chat_completion([{"role": "user", "content": "x"}], max_retries=3)
    msg = str(exc.value)
    assert "401" in msg
    assert "LLM_API_KEY" in msg


def test_5xx_still_retried(fake_llm: FakeLLM, monkeypatch: pytest.MonkeyPatch) -> None:
    # Ingen regression mot T001: 5xx är transient och retras.
    monkeypatch.setattr("mcp_harness.llm.time.sleep", lambda _s: None)
    fake_llm.queue_status(503, times=2)
    fake_llm.queue({"choices": [{"message": {"content": "till slut"}}]})
    result = chat_completion([{"role": "user", "content": "x"}], max_retries=3)
    assert result["choices"][0]["message"]["content"] == "till slut"
    assert len(fake_llm.requests) == 3


def test_5xx_exhausted_actionable(
    fake_llm: FakeLLM, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("mcp_harness.llm.time.sleep", lambda _s: None)
    fake_llm.queue_status(503, times=5)
    with pytest.raises(LlmError) as exc:
        chat_completion([{"role": "user", "content": "x"}], max_retries=3)
    assert "3 försök" in str(exc.value)


def test_timeout_message_actionable() -> None:
    # Ren klassificerare — ingen flakig timing. Timeout pekar på LLM_BASE_URL/last.
    msg = _final_message(TimeoutError("timed out"), timeout=60.0, attempts=3)
    assert "60" in msg
    assert "LLM_BASE_URL" in msg


def test_connection_message_actionable() -> None:
    import urllib.error

    msg = _final_message(
        urllib.error.URLError("Connection refused"), timeout=60.0, attempts=3
    )
    assert "LLM_BASE_URL" in msg


def test_turn_error_carries_curated_message() -> None:
    # run_turn ska använda LlmError-meddelandet verbatim, utan generisk prefix.
    import asyncio

    from mcp_harness.engine import run_turn
    from mcp_harness.events import TurnError

    def boom_llm(_messages: list[dict[str, Any]], _tools: list[dict[str, Any]]) -> dict[str, Any]:
        raise LlmError(
            "LLM timeout: endpoint svarade inte inom 60s — kontrollera LLM_BASE_URL/last."
        )

    async def call_tool(_name: str, _args: dict[str, Any]) -> Any:  # pragma: no cover
        raise AssertionError("ska aldrig nås")

    events = asyncio.run(
        run_turn(
            call_tool=call_tool,
            llm=boom_llm,
            messages=[{"role": "system", "content": "s"}],
            oai_tools=[],
        )
    )
    assert isinstance(events[-1], TurnError)
    assert events[-1].message.startswith("LLM timeout:")
    assert "misslyckades:" not in events[-1].message  # ingen generisk prefix
