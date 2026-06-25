"""T033 — observerbarhet+: latens, token-usage, seed/temperature i params.

Self-describing körningar för regression (PRD §11): mät och registrera, döm inte
(PRD §7). MeteredLlm summerar usage per tur och mäter latens; merge_params
registrerar seed/temperature.
"""

from __future__ import annotations

from mcp_harness.cli import MeteredLlm, merge_params
from tests.conftest import FakeLLM


def test_merge_params_records_seed_and_temperature() -> None:
    assert merge_params(None, 0.0, 42) == {"temperature": 0.0, "seed": 42}


def test_merge_params_preserves_base_and_overrides() -> None:
    assert merge_params({"top_p": 1}, 0.2, None) == {"top_p": 1, "temperature": 0.2}


def test_merge_params_empty_is_none() -> None:
    assert merge_params(None, None, None) is None


def test_metered_llm_captures_usage_and_latency(fake_llm: FakeLLM) -> None:
    fake_llm.queue(
        {
            "choices": [{"message": {"content": "hej"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 3},
        }
    )
    metered = MeteredLlm()
    metered.begin_turn()
    msg = metered([{"role": "user", "content": "x"}], [])
    assert msg["content"] == "hej"
    assert metered.turn_calls == 1
    assert metered.turn_usage == {"prompt_tokens": 10, "completion_tokens": 3}
    assert metered.turn_latency_ms >= 0


def test_metered_llm_sums_usage_across_calls(fake_llm: FakeLLM) -> None:
    for _ in range(2):
        fake_llm.queue({"choices": [{"message": {"content": "x"}}], "usage": {"prompt_tokens": 5}})
    metered = MeteredLlm()
    metered.begin_turn()
    metered([{"role": "user", "content": "a"}], [])
    metered([{"role": "user", "content": "b"}], [])
    assert metered.turn_usage == {"prompt_tokens": 10}
    assert metered.turn_calls == 2
