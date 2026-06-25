"""Människo-läsbart Markdown-transkript — en sink för motorns händelser (T013).

``render_event`` är en ren funktion: händelse → Markdown-fragment. Den är den
*enda* platsen där trunkering sker, och bara för läsbarhet (``…``). Den
maskinläsbara kontraktsytan är JSONL (T020), som bär hela svaret.

``TranscriptSink`` skriver fragmenten löpande (flush) till en fil.
"""

from __future__ import annotations

import json
from typing import TextIO

from .events import (
    AssistantText,
    AttachmentAdded,
    Event,
    ToolCall,
    ToolResult,
    TurnError,
    TurnMeta,
    UserTurn,
)

DEFAULT_TRUNCATE = 500


def render_event(event: Event, *, truncate: int = DEFAULT_TRUNCATE) -> str:
    """Markdown-fragment för en händelse. ``truncate`` gäller endast verktygssvar
    i denna människo-vy — datat (JSONL) trunkeras aldrig."""
    if isinstance(event, UserTurn):
        return f"\n## 👤 Användare\n\n{event.text}"
    if isinstance(event, AssistantText):
        return f"\n## 🤖 Assistent\n\n{event.text}"
    if isinstance(event, ToolCall):
        args = json.dumps(event.arguments, ensure_ascii=False)
        return f"\n- ⚙ `{event.name}({args})`"
    if isinstance(event, ToolResult):
        text = event.text
        shown = text if len(text) <= truncate else text[:truncate] + "…"
        # T015: ett verktygsfel ska se ut som ett fel, inte som ett lyckat svar
        # (princip 3). is_error bor i datat — här gör vi det synligt i vyn.
        marker = "⚠️ " if event.is_error else ""
        return f"  - → {marker}{shown}"
    if isinstance(event, TurnError):
        return f"\n## ⚠️ Fel\n\n{event.message}"
    if isinstance(event, AttachmentAdded):
        return f"\n- 📎 Bilaga: `{event.name}` ({event.kind}, {event.size} B)"
    if isinstance(event, TurnMeta):
        usage = f" · {event.usage}" if event.usage else ""
        return f"\n- ⏱ {event.latency_ms:.0f} ms{usage}"
    # Uttömmande över Event-unionen; en ny händelsetyp ska upptäckas av mypy.
    raise AssertionError(f"okänd händelsetyp: {event!r}")


class TranscriptSink:
    """Skriver renderade händelser löpande till en öppen fil (flushas direkt)."""

    def __init__(self, fh: TextIO, *, truncate: int = DEFAULT_TRUNCATE) -> None:
        self._fh = fh
        self._truncate = truncate

    def write(self, event: Event) -> None:
        self._fh.write(render_event(event, truncate=self._truncate) + "\n")
        self._fh.flush()
