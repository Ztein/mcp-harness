# T044 — exponera test-MCP över Streamable HTTP för riktig E2E

**Status:** DONE · **Fas:** E2E · **Prioritet:** P0 · **Beror på:** T002

## Varför

För **äkta** E2E måste CLI:t köras som det körs på riktigt: en separat process som
talar Streamable HTTP mot en MCP-server (inte in-memory streams). T002:s
fejk-MCP-server måste därför kunna startas fristående och lyssna på en HTTP-port,
så vi kan göra `CLI-process → riktig HTTP → MCP-server` — en kontrollerbar server
med kända verktyg (echo, multi_block, boom, structured) att döma scenarier mot.

## Omfattning

**Ingår:** en körbar test-MCP-server (samma verktyg som T002) som lyssnar på en
Streamable-HTTP-endpoint med bearer-auth (som prod-vägen `MCP_URL`/`MCP_KEY`); en
fixtur/skript som startar den på en ledig port och ger URL+nyckel; så att riktiga
CLI-subprocess-E2E (T040) kan peka `MCP_URL` på den.

**Ingår inte:** att ersätta in-memory-fixturen (T002) — den är fortsatt rätt för
snabba unit-/integrationstester. Detta är den *fristående HTTP*-varianten för E2E.

## Definition of Done

- [ ] Test-MCP-servern kan startas fristående och lyssnar på Streamable HTTP med
      bearer-auth.
- [ ] CLI:t kan ansluta till den via `MCP_URL`/`MCP_KEY` precis som mot en riktig
      server.
- [ ] Samma fyra verktyg (echo, multi_block, boom, structured) exponeras.
- [ ] Fel bearer → avvisas (auth fungerar på riktigt).

## Testfall (skriv först)

1. `test_http_server_lists_tools_over_streamable_http` → en riktig `ClientSession`
   över HTTP ser de fyra verktygen.
2. `test_cli_connects_to_http_test_mcp` → CLI-subprocess ansluter och listar verktyg.
3. `test_wrong_bearer_rejected` → fel nyckel → anslutning nekas (fail-hard).

## Noteringar

Detta är bryggan som gör agent-driven E2E ”på riktigt” möjlig utan en extern,
opålitlig MCP. Den enda kvarvarande externa beroendet för full semantisk dömning
är en riktig LLM-endpoint (fylls i `.env` när scenarierna körs skarpt).
