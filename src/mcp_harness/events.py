"""Strukturerade händelser från en motor-tur (T011).

Motorn producerar dessa i stället för print-strängar. De är den interna
datamodellen som människo-transkriptet (T013) och den maskinläsbara JSONL-loggen
(T020) båda konsumerar — **full trohet** (otrunkerade args/svar) bor här;
trunkering är enbart en vy-angelägenhet.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class UserTurn:
    text: str
    type: Literal["user_turn"] = "user_turn"


@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]  # FULLSTÄNDIGA args — ingen förlust (PRD §11)
    call_id: str
    type: Literal["tool_call"] = "tool_call"


@dataclass
class ToolResult:
    call_id: str
    name: str
    text: str  # konkatenering av ALLA text-block, otrunkerat (T012)
    is_error: bool = False
    block_count: int = 0
    non_text_blocks: int = 0
    structured: dict[str, Any] | None = None
    type: Literal["tool_result"] = "tool_result"


@dataclass
class AssistantText:
    text: str
    type: Literal["assistant_text"] = "assistant_text"


@dataclass
class TurnError:
    message: str
    type: Literal["error"] = "error"


@dataclass
class AttachmentAdded:
    """En bilaga lades till konversationen (T032). Metadata, inte hela innehållet."""

    name: str
    kind: str  # "text" | "image"
    size: int
    type: Literal["attachment"] = "attachment"


Event = UserTurn | ToolCall | ToolResult | AssistantText | TurnError | AttachmentAdded
