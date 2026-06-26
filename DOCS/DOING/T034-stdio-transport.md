# T034 — stdio-transport för MCP

**Status:** DONE · **Fas:** 3 · **Prioritet:** P1 · **Beror på:** T030

## Varför

Många MCP-servrar är **stdio** (startas som en subprocess med `command` + `args`,
pratar över stdin/stdout — som Claude Desktops `mcpServers`), inte HTTP. Idag stöder
harnessen bara Streamable HTTP, så en stor del av MCP-ekosystemet går inte att
testköra. PRD §10 flaggade stdio-prioritet. Arkitekturen är redan förberedd:
anslutningen går via `AsyncExitStack` + `call_tool`-routern (T030), så det räcker
att lägga till en stdio-gren.

## Omfattning

**Ingår:**
- `ServerConfig` får en `transport`-variant: `http` (url/key, default) eller
  `stdio` (command/args/env/cwd).
- `load_servers` parsar stdio-entries; saknat `command` (stdio) eller `url` (http)
  failar hårt (princip 3).
- `_connect_all` grenar på transport: http → `streamable_http_client`; stdio →
  `stdio_client(StdioServerParameters(...))`.
- Allt nedströms (aggregering, routing, fingeravtryck, JSONL, profiler) oförändrat.

**Ingår inte:** SSE-transport (separat vid behov).

## Definition of Done

- [x] `--config` stöder `{"name","transport":"stdio","command","args","env","cwd"}`.
- [x] CLI kan ansluta till en stdio-MCP och lista + anropa verktyg.
- [x] HTTP-vägen oförändrad (regression täckt).
- [x] Trasig config (stdio utan command / http utan url) failar hårt.

## Testfall (skriv först)

1. `test_load_stdio_server` → config med stdio-entry parsas till command/args.
2. `test_stdio_missing_command_fails` → stdio utan command → SystemExit.
3. `test_http_missing_url_fails` → http utan url → SystemExit.
4. `test_stdio_lists_tools_over_subprocess` → starta fejk-MCP som stdio-subprocess
   (`python -m tests.support.fake_mcp --stdio`), anslut med en riktig ClientSession,
   verifiera de fyra verktygen + ett `echo`-anrop. (Riktig E2E, inte mock.)

## Noteringar

I stdio-läge får servern **inte** skriva till stdout (det är protokoll-kanalen) —
bara stderr. Test-MCP:ns `--stdio`-läge måste vara tyst på stdout.
