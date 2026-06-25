"""Rena funktioner för verktygs-menyn: presentation och scoping.

Inga sidoeffekter, ingen I/O — därför enkelt testbara. Menyn modellen ser måste
exakt spegla allowlisten (PRD §11): okänt verktyg failar hårt (princip 3), aldrig
en tyst tom allowlist.
"""

from __future__ import annotations

from typing import Any

from mcp.types import Tool


def to_openai_tools(tools: list[Tool]) -> list[dict[str, Any]]:
    """Konvertera MCP-verktyg till OpenAI-kompatibelt ``tools``-schema.

    ``inputSchema`` skickas oförändrat vidare som ``parameters`` — det är
    kontraktet mot modellen. Tom beskrivning blir ``""`` (inte ``None``)."""
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description or "",
                "parameters": t.inputSchema,
            },
        }
        for t in tools
    ]


def apply_allowlist(tools: list[Tool], allow: set[str] | None) -> list[Tool]:
    """Filtrera verktygen till ``allow`` (per-assistent-scoping, PRD §11).

    ``allow=None`` → alla verktyg. Ett namn i ``allow`` som inte finns failar
    hårt med både det okända och de tillgängliga namnen — ingen tyst tom
    allowlist (princip 3)."""
    if allow is None:
        return list(tools)
    available = {t.name for t in tools}
    unknown = allow - available
    if unknown:
        raise SystemExit(f"--tools: okända verktyg {sorted(unknown)}; finns: {sorted(available)}")
    return [t for t in tools if t.name in allow]
