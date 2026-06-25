#!/usr/bin/env python3
"""mcp-harness — testkör en MCP genom en riktig LLM + systemprompt i terminalen.

Tunn I/O-skal: argument-parsing, anslutning och utskrift. Själva agent-loopen bor
i :mod:`mcp_harness.engine` (testbar), människo-transkriptet i
:mod:`mcp_harness.transcript`, verktygs-menyn i :mod:`mcp_harness.tools`.

Generisk: funkar mot vilken Streamable-HTTP-MCP som helst och vilken
OpenAI-kompatibel modell som helst. LLM-config är provider-agnostisk
(LLM_BASE_URL/_API_KEY/_MODEL) — se :mod:`mcp_harness.llm`.

Kommandon i chatten: /tools (lista verktyg), /reset (nollställ historik), /quit.
Piped stdin funkar också (en rad = en tur, avslutar vid EOF).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, TextIO

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from .engine import LlmFn, run_turn
from .events import AssistantText, Event, ToolCall, ToolResult, TurnError, UserTurn
from .llm import chat_completion, llm_model
from .tools import apply_allowlist, to_openai_tools
from .transcript import TranscriptSink

DEFAULT_SYSTEM = (
    "Du är en assistent med verktyg mot Azure DevOps. Använd verktygen när det behövs "
    "och svara kort och tydligt på svenska."
)


def _load_system(system_arg: str | None) -> str:
    """Systemprompt (skill). Prioritet: --system <fil> > MCP_CHAT_SYSTEM_FILE >
    MCP_CHAT_SYSTEM (sträng) > inbyggd default. .md-filen läses in direkt."""
    path = system_arg or os.environ.get("MCP_CHAT_SYSTEM_FILE")
    if path:
        return Path(path).read_text(encoding="utf-8")
    return os.environ.get("MCP_CHAT_SYSTEM", DEFAULT_SYSTEM)


def _llm_message(messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
    """En LlmFn: ett chat/completions-anrop via den provider-agnostiska klienten;
    returnerar assistent-meddelandet (det motorn arbetar med)."""
    choice: dict[str, Any] = chat_completion(messages, tools, timeout=120)["choices"][0]
    message: dict[str, Any] = choice["message"]
    return message


async def _read(prompt: str) -> str | None:
    try:
        return (await asyncio.to_thread(input, prompt)).strip()
    except EOFError:
        return None


def _open_transcript(path_arg: str | None) -> TextIO:
    """Öppna transkriptfil (människoläsbar md). --transcript > MCP_CHAT_TRANSCRIPT_DIR
    > default transcripts/chat-<tidsstämpel>.md. Skrivs löpande (flush)."""
    if path_arg:
        path = Path(path_arg)
    else:
        directory = Path(os.environ.get("MCP_CHAT_TRANSCRIPT_DIR", "transcripts"))
        path = directory / f"chat-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    fh = path.open("a", encoding="utf-8")
    fh.write(f"# Chatt-transkript {datetime.now().isoformat(timespec='seconds')}\n\n")
    fh.write(f"- MCP: {os.environ.get('MCP_URL', '?')}\n- Modell: {llm_model()}\n")
    fh.flush()
    print(f"Transkript: {path}")
    return fh


def _print_event(event: Event) -> None:
    """Lättviktig stdout-vy av en motor-händelse (transkriptet bär den fulla)."""
    if isinstance(event, ToolCall):
        print(f"  ⚙ {event.name}({json.dumps(event.arguments, ensure_ascii=False)})")
    elif isinstance(event, ToolResult):
        if event.is_error:
            print(f"    {event.text}")
    elif isinstance(event, AssistantText):
        print(f"\n{event.text}")
    elif isinstance(event, TurnError):
        print(f"\n⚠️  {event.message}")


async def main(
    system: str,
    transcript: TranscriptSink,
    tools_allow: set[str] | None = None,
    *,
    llm: LlmFn = _llm_message,
) -> None:
    url, key = os.environ["MCP_URL"], os.environ["MCP_KEY"]
    async with (
        streamablehttp_client(url, headers={"Authorization": f"Bearer {key}"}) as (r, w, _),
        ClientSession(r, w) as session,
    ):
        await session.initialize()
        # Per-assistent-scoping (PRD §11): menyn modellen ser speglar exakt
        # allowlisten; okänt namn failar hårt (princip 3). Se tools.py.
        mcp_tools = apply_allowlist((await session.list_tools()).tools, tools_allow)
        oai_tools = to_openai_tools(mcp_tools)
        print(f"Ansluten: {url} — {len(mcp_tools)} verktyg, modell {llm_model()}.")
        print(f"Systemprompt: {len(system)} tecken.")
        print("Skriv ditt meddelande (/tools, /reset, /quit).")

        messages: list[dict[str, Any]] = [{"role": "system", "content": system}]
        while True:
            user = await _read("\n> ")
            if user is None or user in ("/quit", "/exit"):
                print("Hej då.")
                return
            if not user:
                continue
            if user == "/tools":
                print("\n".join(f"  - {t.name}" for t in mcp_tools))
                continue
            if user == "/reset":
                messages = [{"role": "system", "content": system}]
                print("(historik nollställd)")
                continue

            messages.append({"role": "user", "content": user})
            transcript.write(UserTurn(text=user))
            events = await run_turn(
                session=session, llm=llm, messages=messages, oai_tools=oai_tools
            )
            for event in events:
                _print_event(event)
                transcript.write(event)


def cli() -> None:
    """Entry point (mcp-harness). MVP: en MCP-server via MCP_URL/MCP_KEY, en
    systemprompt, en allowlist. PRD beskriver vart det är på väg (flera servrar,
    harness-profiler, fil-uppladdning)."""
    parser = argparse.ArgumentParser(
        description="mcp-harness — testkör en MCP genom en riktig LLM + systemprompt i terminalen."
    )
    parser.add_argument(
        "--system", help="Sökväg till en .md-fil med systemprompt (skill/persona) som läses in."
    )
    parser.add_argument(
        "--transcript", help="Sökväg för transkriptfil (default transcripts/chat-<tidsstämpel>.md)."
    )
    parser.add_argument(
        "--tools",
        help="Kommaseparerad allowlist av verktygsnamn (approximerar per-assistent-scoping). "
        "Default: alla verktyg servern exponerar.",
    )
    args = parser.parse_args()
    tools_allow = {t.strip() for t in args.tools.split(",") if t.strip()} if args.tools else None
    fh = _open_transcript(args.transcript)
    try:
        asyncio.run(main(_load_system(args.system), TranscriptSink(fh), tools_allow))
    finally:
        fh.close()


if __name__ == "__main__":
    cli()
