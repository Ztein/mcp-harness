"""T020 — maskinläsbar JSONL-körlogg.

Den versionerade kontraktsytan test-agenten bygger sin loop på (PRD §11): en rad
per händelse, **fullständiga** args, **otrunkerade** svar. Trunkering hör bara
hemma i människo-vyn (T013), aldrig här.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

from mcp_harness.events import AssistantText, ToolCall, ToolResult, UserTurn
from mcp_harness.jsonl import SCHEMA_VERSION, JsonlSink


def _records(buf: io.StringIO) -> list[dict[str, object]]:
    return [json.loads(line) for line in buf.getvalue().splitlines() if line.strip()]


def test_jsonl_one_object_per_line() -> None:
    buf = io.StringIO()
    sink = JsonlSink(buf)
    sink.write(UserTurn(text="hej"))
    sink.write(ToolCall(name="echo", arguments={"text": "x"}, call_id="c1"))
    sink.write(ToolResult(call_id="c1", name="echo", text="x"))
    sink.write(AssistantText(text="svar"))
    recs = _records(buf)
    assert [r["type"] for r in recs] == ["user_turn", "tool_call", "tool_result", "assistant_text"]


def test_jsonl_tool_result_untruncated() -> None:
    buf = io.StringIO()
    big = "y" * 2000  # längre än människo-vyns klipp (500)
    JsonlSink(buf).write(ToolResult(call_id="c1", name="echo", text=big))
    assert _records(buf)[0]["text"] == big


def test_jsonl_tool_call_full_args() -> None:
    buf = io.StringIO()
    args = {"a": "x" * 1000, "nested": {"b": [1, 2, 3], "c": "åäö"}}
    JsonlSink(buf).write(ToolCall(name="echo", arguments=args, call_id="c1"))
    assert _records(buf)[0]["arguments"] == args


def test_jsonl_has_schema_version() -> None:
    buf = io.StringIO()
    sink = JsonlSink(buf)
    sink.write_header(model="m", mcp_url="u")
    sink.write(UserTurn(text="hej"))
    recs = _records(buf)
    assert recs and all(r["schema_version"] == SCHEMA_VERSION for r in recs)


def test_jsonl_header_fields() -> None:
    buf = io.StringIO()
    JsonlSink(buf).write_header(
        model="gemma", params={"temperature": 0}, mcp_url="http://x/mcp", tools=["echo", "boom"]
    )
    rec = _records(buf)[0]
    assert rec["type"] == "run_header"
    assert rec["model"] == "gemma"
    assert rec["tools"] == ["echo", "boom"]


def test_jsonl_flushed_incrementally(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    fh = path.open("w", encoding="utf-8")
    sink = JsonlSink(fh)
    sink.write(UserTurn(text="först"))
    # Läs filen mitt i körningen — raden ska redan finnas på disk.
    assert "först" in path.read_text(encoding="utf-8")
    fh.close()
