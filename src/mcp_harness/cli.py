#!/usr/bin/env python3
"""Liten terminal-chattklient: prata med en LLM som kan köra MCP-verktyg.
Multi-turn — modellen kan kedja flera verktygsanrop per svar.

Generisk: funkar mot vilken Streamable-HTTP-MCP som helst och vilken
OpenAI-kompatibel modell som helst. LLM-config är provider-agnostisk
(LLM_BASE_URL/_API_KEY/_MODEL) — se llm_client.py.

    set -a; source .env; set +a                       # LLM_BASE_URL/_API_KEY/_MODEL
    export MCP_URL=http://<host>/mcp
    export MCP_KEY=<MCP API-nyckel>
    uv run python scripts/mcp_chat.py

Kommandon i chatten: /tools (lista verktyg), /reset (nollställ historik),
/quit. Piped stdin funkar också (kör ett gäng rader, avslutar vid EOF).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import TextIO

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from .llm import chat_completion, llm_model

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


def _llm(messages: list[dict], tools: list[dict]) -> dict:
    """Ett chat/completions-anrop via den provider-agnostiska klienten;
    returnerar choices[0] (det chatten använder)."""
    return chat_completion(messages, tools, model=None, timeout=120)["choices"][0]


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


def _w(tr: TextIO, text: str) -> None:
    tr.write(text + "\n")
    tr.flush()


async def main(system: str, tr: TextIO, tools_allow: set[str] | None = None) -> None:
    url, key = os.environ["MCP_URL"], os.environ["MCP_KEY"]
    async with (
        streamablehttp_client(url, headers={"Authorization": f"Bearer {key}"}) as (r, w, _),
        ClientSession(r, w) as session,
    ):
        await session.initialize()
        mcp_tools = (await session.list_tools()).tools
        if tools_allow is not None:
            # Per-assistent-scoping (T178): visa bara en delmängd av verktygen för
            # modellen, så scoping-effekten kan valideras via terminalen utan Intric.
            # Okänt namn failar högljutt (princip 2) — ingen tyst tom allowlist.
            available = {t.name for t in mcp_tools}
            unknown = tools_allow - available
            if unknown:
                raise SystemExit(
                    f"--tools: okända verktyg {sorted(unknown)}; finns: {sorted(available)}"
                )
            mcp_tools = [t for t in mcp_tools if t.name in tools_allow]
        oai_tools = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description or "",
                    "parameters": t.inputSchema,
                },
            }
            for t in mcp_tools
        ]
        print(f"Ansluten: {url} — {len(mcp_tools)} verktyg, modell {llm_model()}.")
        print(f"Systemprompt: {len(system)} tecken.")
        print("Skriv ditt meddelande (/tools, /reset, /quit).")

        messages: list[dict] = [{"role": "system", "content": system}]
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
            _w(tr, f"\n## 👤 Användare\n\n{user}")
            # Agent-loop: kör verktyg tills modellen ger ett textsvar.
            while True:
                try:
                    choice = _llm(messages, oai_tools)
                except Exception as exc:  # transient LLM-fel: logga, krascha ej
                    err = f"LLM-anrop misslyckades: {exc}"
                    print(f"\n⚠️  {err}\n   Skriv om eller försök igen.")
                    _w(tr, f"\n## ⚠️ Fel\n\n{err}")
                    break
                msg = choice["message"]
                tool_calls = msg.get("tool_calls")
                if not tool_calls:
                    content = msg.get("content") or "(tomt svar)"
                    print(f"\n{content}")
                    _w(tr, f"\n## 🤖 Assistent\n\n{content}")
                    messages.append({"role": "assistant", "content": msg.get("content")})
                    break
                messages.append(
                    {"role": "assistant", "content": msg.get("content"), "tool_calls": tool_calls}
                )
                for tc in tool_calls:
                    name = tc["function"]["name"]
                    args = json.loads(tc["function"].get("arguments") or "{}")
                    print(f"  ⚙ {name}({json.dumps(args, ensure_ascii=False)})")
                    _w(tr, f"\n- ⚙ `{name}({json.dumps(args, ensure_ascii=False)})`")
                    try:
                        result = await session.call_tool(name, args)
                        text = result.content[0].text if result.content else "(tomt)"
                    except Exception as exc:
                        text = f"FEL vid verktygsanrop: {exc}"
                        print(f"    {text}")
                    _w(tr, f"  - → {text[:500]}")
                    messages.append({"role": "tool", "tool_call_id": tc["id"], "content": text})


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
    transcript = _open_transcript(args.transcript)
    try:
        asyncio.run(main(_load_system(args.system), transcript, tools_allow))
    finally:
        transcript.close()


if __name__ == "__main__":
    cli()
