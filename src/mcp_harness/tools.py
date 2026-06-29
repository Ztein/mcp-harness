"""Rena funktioner för verktygs-menyn: presentation och scoping.

Inga sidoeffekter, ingen I/O — därför enkelt testbara. Menyn modellen ser måste
exakt spegla allowlisten (PRD §11): okänt verktyg failar hårt (princip 3), aldrig
en tyst tom allowlist.
"""

from __future__ import annotations

import hashlib
import json
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


def aggregate_tools(per_server: list[tuple[str, list[Tool]]]) -> tuple[list[Tool], dict[str, str]]:
    """Slå ihop verktyg från flera servrar till en meny (PRD §6.2).

    Returnerar (aggregerade verktyg, {verktygsnamn: servernamn}). En namn-krock
    failar hårt med båda servrarna namngivna — aldrig tyst överskuggning
    (princip 3)."""
    tools: list[Tool] = []
    owner: dict[str, str] = {}
    for server_name, server_tools in per_server:
        for t in server_tools:
            if t.name in owner:
                raise SystemExit(
                    f"verktygs-namnkrock: '{t.name}' finns i både '{owner[t.name]}' "
                    f"och '{server_name}' — ge servrarna distinkta verktyg eller koppla in färre."
                )
            owner[t.name] = server_name
            tools.append(t)
    return tools, owner


def tools_fingerprint(tools: list[Tool]) -> str:
    """Stabil hash av verktygsmenyn (namn + beskrivning + inputSchema).

    Beräknas på menyn modellen faktiskt ser (efter allowlist/scoping). Stabil
    mellan körningar för samma schema, ändras när ett verktygs schema ändras — så
    en stale server (rätt antal, gammal kod) inte kan maskera sig (PRD §11).
    Ordnings-oberoende: verktygen sorteras på namn."""
    canon = [
        {"name": t.name, "description": t.description or "", "schema": t.inputSchema}
        for t in sorted(tools, key=lambda t: t.name)
    ]
    blob = json.dumps(canon, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def tool_surface(tools: list[Tool]) -> list[dict[str, Any]]:
    """Maskinläsbar dump av hela verktygsytan (T025): namn, beskrivning, parametrar.

    Klartext-komplement till ``tools_fingerprint`` — fingeravtrycket svarar på *att*
    ytan ändrats, det här på *vad* den bestod av. Sorterad på namn (stabil mellan
    körningar). Beräknas på menyn modellen faktiskt ser (efter allowlist/scoping)."""
    return [
        {"name": t.name, "description": t.description or "", "parameters": t.inputSchema}
        for t in sorted(tools, key=lambda t: t.name)
    ]


def render_tool_surface(tools: list[Tool], *, as_json: bool) -> str:
    """Formatera verktygsytan för utskrift: JSON för maskiner, kort lista för människor."""
    surface = tool_surface(tools)
    if as_json:
        return json.dumps(surface, ensure_ascii=False, indent=2, sort_keys=True)
    lines: list[str] = []
    for entry in surface:
        desc = str(entry["description"]).strip().splitlines()
        head = f"- {entry['name']}" + (f" — {desc[0]}" if desc else "")
        lines.append(head)
        props = (entry["parameters"] or {}).get("properties") or {}
        for pname in sorted(props):
            ptype = (props[pname] or {}).get("type", "?")
            lines.append(f"    · {pname}: {ptype}")
    return "\n".join(lines)


def check_expected_tools(tools: list[Tool], expected: set[str]) -> None:
    """Failar hårt om verktygsmängden avviker från ``expected`` (exakt mängd).

    Både saknade och oväntade verktyg listas (princip 3). Match → tyst retur."""
    actual = {t.name for t in tools}
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing or unexpected:
        raise SystemExit(
            f"--expect-tools avvikelse — saknade: {missing}; oväntade: {unexpected}; "
            f"faktiska: {sorted(actual)}"
        )
