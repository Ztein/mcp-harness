"""Maskinläsbar JSONL-körlogg (T020) — produktens versionerade kontraktsyta.

En rad per händelse, **fullständiga** args och **otrunkerade** svar (princip 3,
PRD §11). En valfri ``run_header``-rad bär modell, params, MCP-URL och verktygs-
menyn (server-fingeravtryck (T021) och profil (T031) hängs på i headern senare).

Ändra aldrig betydelsen av ett fält utan att bumpa :data:`SCHEMA_VERSION`.
Schemat dokumenteras i ``docs/jsonl-schema.md``.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, TextIO

from .events import Event

SCHEMA_VERSION = 1


class JsonlSink:
    """Skriver händelser (och en valfri header) som JSON-rader, flushat löpande."""

    def __init__(self, fh: TextIO) -> None:
        self._fh = fh

    def write_header(self, **meta: Any) -> None:
        """Skriv en ``run_header``-rad. ``meta`` t.ex. model, params, mcp_url, tools."""
        self._emit({"type": "run_header", **meta})

    def write(self, event: Event) -> None:
        """Skriv en händelse oavkortat (asdict bevarar fulla args/svar)."""
        self._emit(asdict(event))

    def _emit(self, record: dict[str, Any]) -> None:
        # schema_version först — varje rad är självbeskrivande och versionerad.
        line = json.dumps({"schema_version": SCHEMA_VERSION, **record}, ensure_ascii=False)
        self._fh.write(line + "\n")
        self._fh.flush()
