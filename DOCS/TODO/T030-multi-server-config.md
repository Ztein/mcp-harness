# T030 — flera MCP-servrar via config

**Status:** TODO · **Fas:** 3 · **Prioritet:** P1 · **Beror på:** T010, T021

## Varför

PRD §6.2 / Fas 1: en MCP beter sig olika beroende på hur många servrar som är
inkopplade samtidigt (verktygs-antalet påverkar modellens val). Idag stöds bara
**en** server via `MCP_URL`/`MCP_KEY`. Vi behöver en config-fil som listar flera
servrar (likt Claude Desktops `mcpServers`) och aggregerar verktygen till en meny.

## Omfattning

**Ingår:** en config-fil (`mcp.json`/`mcp.toml`) med namngivna servrar: transport
(Streamable HTTP först), URL, auth. Verktygs-aggregering med **namn-krock-
hantering** (deterministisk prefixning eller fail-hard). Fingeravtrycket (T021)
beräknas på den aggregerade menyn.

**Ingår inte:** stdio-/SSE-transport (egen uppföljnings-ticket; PRD §10 noterar
stdio-prioritet).

## Definition of Done

- [ ] Config-fil läser flera Streamable-HTTP-servrar.
- [ ] Verktyg aggregeras; namn-krockar hanteras deterministiskt och **synligt**
      (aldrig tyst överskuggning).
- [ ] Saknad/trasig config failar hårt med tydligt meddelande.
- [ ] JSONL-headern (T020) listar alla anslutna servrar + per-server-fingeravtryck.

## Testfall (skriv först)

1. `test_two_servers_tools_aggregated` → två fejk-MCP-servrar → menyn innehåller
   bådas verktyg.
2. `test_name_collision_handled_visibly` → två servrar med samma verktygsnamn →
   deterministisk disambiguering (eller fail-hard), aldrig tyst tappat verktyg.
3. `test_broken_config_fails_loudly` → ogiltig config → `SystemExit` med tydligt fel.

## Noteringar

Bryt ut detaljerade testfall när Fas 2 är klar — beroendena (T021-fingeravtryck)
kan ändra exakt form. Håll config:en data, inte kod (princip 1).
