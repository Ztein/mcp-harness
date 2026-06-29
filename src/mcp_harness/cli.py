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
import sys
import time
from contextlib import AsyncExitStack
from datetime import datetime
from pathlib import Path
from typing import Any, TextIO

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import (  # type: ignore[attr-defined]  # create_mcp_http_client ej i mcp:s __all__
    create_mcp_http_client,
    streamable_http_client,
)

from .attachments import Attachment, build_user_content, load_attachment
from .config import ServerConfig, load_servers
from .engine import DEFAULT_MAX_TOOL_CALLS, LlmFn, RunSummary, run_turn, tally_turn
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
from .jsonl import JsonlSink
from .llm import chat_completion, llm_model
from .profiles import frame_system, load_profile
from .tools import (
    aggregate_tools,
    apply_allowlist,
    check_expected_tools,
    render_tool_surface,
    to_openai_tools,
    tools_fingerprint,
)
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
    choice: dict[str, Any] = chat_completion(messages, tools)["choices"][0]
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
            print(f"    ⚠️  {event.text}")
    elif isinstance(event, AssistantText):
        print(f"\n{event.text}")
    elif isinstance(event, TurnError):
        print(f"\n⚠️  {event.message}")


def _llm_params() -> dict[str, Any] | None:
    """Ev. extra LLM-params (LLM_PARAMS) för JSONL-headern — None om osatt/ogiltig."""
    raw = os.environ.get("LLM_PARAMS", "").strip()
    if not raw:
        return None
    try:
        parsed: dict[str, Any] = json.loads(raw)
        return parsed
    except json.JSONDecodeError:
        return None


def merge_params(
    base: dict[str, Any] | None, temperature: float | None, seed: int | None
) -> dict[str, Any] | None:
    """Slå ihop bas-params med ev. --temperature/--seed (registreras i headern, T033)."""
    params = dict(base or {})
    if temperature is not None:
        params["temperature"] = temperature
    if seed is not None:
        params["seed"] = seed
    return params or None


class MeteredLlm:
    """LlmFn-wrapper som mäter latens och summerar token-usage per tur (T033).

    Mäter och *registrerar* — dömer inte (PRD §7). ``begin_turn`` nollställer
    ackumulatorerna inför varje tur."""

    def __init__(self, extra_params: dict[str, Any] | None = None, timeout: float = 60.0) -> None:
        self._extra = extra_params or None
        self._timeout = timeout
        self.turn_latency_ms = 0.0
        self.turn_usage: dict[str, float] = {}
        self.turn_calls = 0

    def begin_turn(self) -> None:
        self.turn_latency_ms = 0.0
        self.turn_usage = {}
        self.turn_calls = 0

    def __call__(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> dict[str, Any]:
        t0 = time.monotonic()
        resp = chat_completion(messages, tools, timeout=self._timeout, extra=self._extra)
        self.turn_latency_ms += (time.monotonic() - t0) * 1000
        self.turn_calls += 1
        for key, value in (resp.get("usage") or {}).items():
            if isinstance(value, int | float):
                self.turn_usage[key] = self.turn_usage.get(key, 0) + value
        message: dict[str, Any] = resp["choices"][0]["message"]
        return message


async def _connect_all(
    stack: AsyncExitStack, servers: list[ServerConfig]
) -> tuple[dict[str, ClientSession], list[tuple[str, list[Any]]]]:
    """Anslut till alla servrar och returnera (session per namn, verktyg per server)."""
    sessions: dict[str, ClientSession] = {}
    per_server: list[tuple[str, list[Any]]] = []
    for srv in servers:
        if srv.transport == "stdio":
            # Starta servern som subprocess och prata över stdin/stdout (T034).
            params = StdioServerParameters(
                command=srv.command, args=srv.args, env=srv.env, cwd=srv.cwd
            )
            r, w = await stack.enter_async_context(stdio_client(params))
        else:
            http_client = await stack.enter_async_context(
                create_mcp_http_client(headers={"Authorization": f"Bearer {srv.key}"})
            )
            r, w, _ = await stack.enter_async_context(
                streamable_http_client(srv.url, http_client=http_client)
            )
        session = await stack.enter_async_context(ClientSession(r, w))
        await session.initialize()
        sessions[srv.name] = session
        per_server.append((srv.name, list((await session.list_tools()).tools)))
    return sessions, per_server


async def dump_tool_surface(
    servers: list[ServerConfig], tools_allow: set[str] | None, *, as_json: bool
) -> str:
    """Anslut, aggregera och scope:a verktygsytan, och rendera den (T025).

    Non-interaktivt: inget LLM-anrop, ingen tur. För att versionsstämpla *vilken
    yta som testades* (namn + beskrivning + parametrar) i en scriptad körning."""
    async with AsyncExitStack() as stack:
        _, per_server = await _connect_all(stack, servers)
        all_tools, _ = aggregate_tools(per_server)
        mcp_tools = apply_allowlist(all_tools, tools_allow)
        return render_tool_surface(mcp_tools, as_json=as_json)


async def main(
    system: str,
    transcript: TranscriptSink,
    servers: list[ServerConfig],
    tools_allow: set[str] | None = None,
    *,
    llm: LlmFn = _llm_message,
    jsonl: JsonlSink | None = None,
    expect_tools: set[str] | None = None,
    max_tool_calls: int = DEFAULT_MAX_TOOL_CALLS,
    profile_name: str = "raw",
    approximation_note: str = "",
    attachments: list[Attachment] | None = None,
    params: dict[str, Any] | None = None,
    fail_on_tool_error: bool = False,
) -> RunSummary:
    async with AsyncExitStack() as stack:
        sessions, per_server = await _connect_all(stack, servers)
        # Aggregera menyn över alla servrar; namn-krock failar hårt (PRD §6.2).
        all_tools, owner = aggregate_tools(per_server)
        # Per-assistent-scoping (PRD §11): menyn modellen ser speglar exakt allowlisten.
        mcp_tools = apply_allowlist(all_tools, tools_allow)
        # Fail-hard mot stale server (PRD §11, T021) innan ett enda LLM-anrop.
        if expect_tools is not None:
            check_expected_tools(mcp_tools, expect_tools)
        fingerprint = tools_fingerprint(mcp_tools)
        oai_tools = to_openai_tools(mcp_tools)
        names = sorted(t.name for t in mcp_tools)

        async def call_tool(name: str, args: dict[str, Any]) -> Any:
            # Routa till den server som äger verktyget (T030).
            return await sessions[owner[name]].call_tool(name, args)

        servers_desc = ", ".join(f"{s.name}({s.url})" for s in servers)
        print(
            f"Ansluten: {len(servers)} server(rar) [{servers_desc}] — "
            f"{len(mcp_tools)} verktyg, modell {llm_model()}."
        )
        print(f"Verktyg: {', '.join(names)}")
        print(f"Fingeravtryck: {fingerprint}")
        print(f"Profil: {profile_name}")
        if approximation_note:
            # Ärlig not (PRD §11): en grön körning är inte 'verifierad i den riktiga harnessen'.
            print(f"  ⓘ {approximation_note}")
        print(f"Systemprompt: {len(system)} tecken.")
        print("Skriv ditt meddelande (/tools, /reset, /quit).")

        if jsonl is not None:
            # Självbeskrivande körning (PRD §11): modell, params, servrar, meny, profil.
            jsonl.write_header(
                model=llm_model(),
                params=params if params is not None else _llm_params(),
                mcp_url=",".join(s.url for s in servers),
                servers=[s.name for s in servers],
                tools=names,
                tools_fingerprint=fingerprint,
                profile=profile_name,
                approximation_note=approximation_note,
                system_chars=len(system),
            )

        def emit(event: Event) -> None:
            transcript.write(event)
            if jsonl is not None:
                jsonl.write(event)

        # Bilagor som väntar på att matas in i nästa tur (--attach + /attach, T032).
        pending: list[Attachment] = list(attachments or [])
        for a in pending:
            emit(AttachmentAdded(name=a.name, kind=a.kind, size=a.size))

        # Headless: i piped läge (ingen TTY) skrivs ingen interaktiv prompt som
        # annars skräpar ner loggen (T022).
        prompt = "\n> " if sys.stdin.isatty() else ""
        summary = RunSummary(fail_on_tool_error=fail_on_tool_error)
        messages: list[dict[str, Any]] = [{"role": "system", "content": system}]
        while True:
            user = await _read(prompt)
            if user is None or user in ("/quit", "/exit"):
                print("Hej då.")
                print(summary.line())
                return summary
            if not user:
                continue
            if user == "/tools":
                print("\n".join(f"  - {t.name}" for t in mcp_tools))
                continue
            if user == "/reset":
                messages = [{"role": "system", "content": system}]
                pending = []
                print("(historik nollställd)")
                continue
            if user.startswith("/attach "):
                try:
                    a = load_attachment(user[len("/attach ") :].strip())
                except SystemExit as exc:  # ogiltig bilaga ska inte döda sessionen
                    print(f"  {exc}")
                    continue
                pending.append(a)
                emit(AttachmentAdded(name=a.name, kind=a.kind, size=a.size))
                print(f"  📎 {a.name} ({a.kind}, {a.size} B) — matas in i nästa tur.")
                continue

            messages.append({"role": "user", "content": build_user_content(user, pending)})
            pending = []  # förbrukade i denna tur
            emit(UserTurn(text=user))
            if isinstance(llm, MeteredLlm):
                llm.begin_turn()
            started = time.monotonic()
            events = await run_turn(
                call_tool=call_tool,
                llm=llm,
                messages=messages,
                oai_tools=oai_tools,
                max_tool_calls=max_tool_calls,
            )
            latency_ms = (time.monotonic() - started) * 1000
            tally_turn(summary, events)
            for event in events:
                _print_event(event)
                emit(event)
            # Mät och registrera per tur (T033) — döm inte (PRD §7).
            if isinstance(llm, MeteredLlm):
                emit(
                    TurnMeta(
                        latency_ms=round(latency_ms, 1),
                        llm_calls=llm.turn_calls,
                        usage=llm.turn_usage or None,
                    )
                )
            else:
                emit(TurnMeta(latency_ms=round(latency_ms, 1)))


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
    parser.add_argument(
        "--jsonl",
        help="Sökväg för maskinläsbar JSONL-körlogg (en rad/händelse, otrunkerat). "
        "Den stabila kontraktsytan för agent-/regressionstestning.",
    )
    parser.add_argument(
        "--expect-tools",
        help="Kommaseparerad förväntad verktygsmängd (exakt). Avvikelse failar högljutt "
        "innan något LLM-anrop — stoppar en stale server från att maskera sig.",
    )
    parser.add_argument(
        "--max-tool-calls-per-turn",
        type=int,
        default=DEFAULT_MAX_TOOL_CALLS,
        help=f"Tak på verktygsanrop per tur (backstop mot loopande modell). "
        f"Default {DEFAULT_MAX_TOOL_CALLS}.",
    )
    parser.add_argument(
        "--config",
        help="JSON-fil med flera MCP-servrar ({'servers':[{name,url,key}]}). "
        "Default: en server via MCP_URL/MCP_KEY.",
    )
    parser.add_argument(
        "--profile",
        default="raw",
        help="Harness-profil (profiles/<namn>.json eller sökväg). Ramar skillen och "
        "kan scope:a verktyg. Default: raw (ingen extra ramning).",
    )
    parser.add_argument(
        "--attach",
        action="append",
        metavar="FIL",
        help="Bifoga en fil till första turen (text inline, bild multimodalt). "
        "Kan upprepas. Även /attach <fil> i chatten.",
    )
    parser.add_argument(
        "--temperature", type=float, help="Sätt temperature och registrera den i JSONL-headern."
    )
    parser.add_argument(
        "--seed", type=int, help="Sätt seed (där modellen tillåter) och registrera den i headern."
    )
    parser.add_argument(
        "--fail-on-tool-error",
        action="store_true",
        help="Låt ett verktygsfel (is_error) grinda körningen rött (exit≠0). "
        "Default: tool-fel rapporteras i sammanfattningen men ändrar inte exit-koden.",
    )
    parser.add_argument(
        "--list-tools",
        action="store_true",
        help="Anslut, skriv ut hela verktygsytan (namn, beskrivning, parametrar) och "
        "avsluta. Inget LLM-anrop, ingen tur. Respekterar --tools/--profile-scoping.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Maskinläsbar JSON-utdata för --list-tools (annars en kort lista).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Per-anrops-timeout mot LLM-endpointen i sekunder (default 60). "
        "Lägre = snabbare, tydligare fail i agent-/regressionskörning.",
    )
    args = parser.parse_args()
    profile = load_profile(args.profile)
    # Profilen ramar skillen (runt, inte över) och kan scope:a verktyg.
    system = frame_system(profile, _load_system(args.system))
    if args.tools:
        tools_allow: set[str] | None = {t.strip() for t in args.tools.split(",") if t.strip()}
    elif profile.tools_allow:
        tools_allow = set(profile.tools_allow)
    else:
        tools_allow = None
    expect_tools = (
        {t.strip() for t in args.expect_tools.split(",") if t.strip()}
        if args.expect_tools
        else None
    )
    if args.config:
        servers = load_servers(args.config)
    else:
        mcp_url, mcp_key = os.environ.get("MCP_URL"), os.environ.get("MCP_KEY")
        if not mcp_url or not mcp_key:
            raise SystemExit("❌ MCP_URL/MCP_KEY saknas — sätt dem eller använd --config.")
        servers = [ServerConfig(name="default", url=mcp_url, key=mcp_key)]
    if args.list_tools:
        # Non-interaktiv ytdump (T025): anslut, skriv schemat, avsluta. Inget LLM,
        # ingen transkript-fil — så scriptade körningar kan versionsstämpla ytan.
        print(asyncio.run(dump_tool_surface(servers, tools_allow, as_json=args.json)))
        raise SystemExit(0)
    # Self-describing körning (T033): registrera seed/temperature och mät per tur.
    params = merge_params(_llm_params(), args.temperature, args.seed)
    metered_llm = MeteredLlm(params, timeout=args.timeout)
    fh = _open_transcript(args.transcript)
    jsonl_fh = open(args.jsonl, "a", encoding="utf-8") if args.jsonl else None
    jsonl_sink = JsonlSink(jsonl_fh) if jsonl_fh is not None else None
    try:
        summary = asyncio.run(
            main(
                system,
                TranscriptSink(fh),
                servers,
                tools_allow,
                llm=metered_llm,
                jsonl=jsonl_sink,
                expect_tools=expect_tools,
                max_tool_calls=args.max_tool_calls_per_turn,
                profile_name=profile.name,
                approximation_note=profile.approximation_note,
                attachments=[load_attachment(f) for f in (args.attach or [])],
                params=params,
                fail_on_tool_error=args.fail_on_tool_error,
            )
        )
    finally:
        fh.close()
        if jsonl_fh is not None:
            jsonl_fh.close()
    # Ren exit-kod: ≠0 om någon tur slutligen misslyckades (PRD §11).
    raise SystemExit(summary.exit_code)


if __name__ == "__main__":
    cli()
