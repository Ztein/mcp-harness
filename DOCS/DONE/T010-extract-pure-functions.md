# T010 — bryt ut rena funktioner (schema-konvertering, allowlist)

**Status:** DONE · **Fas:** 1 · **Prioritet:** P1 · **Beror på:** T002

## Varför

`main()` i [cli.py](../../src/mcp_harness/cli.py) gör allt: MCP-anslutning,
schema-konvertering, allowlist-filtrering, agent-loop, I/O och transkript i en
enda async-funktion. Det går inte att enhetstesta. Första refaktor-steget är att
lyfta ut de **rena** bitarna (MCP-verktyg → OpenAI-verktygsschema; allowlist-
filtrering) till funktioner utan sidoeffekter, under tester. PRD §11 kräver att
menyn modellen ser **exakt** speglar profilen/allowlisten — det måste vara testat.

## Omfattning

**Ingår:** funktioner `to_openai_tools(mcp_tools) -> list[dict]` och
`apply_allowlist(mcp_tools, allow) -> list[mcp_tools]` (failar hårt på okänt namn,
som idag). Karaktäriseringstester först som låser nuvarande korrekta beteende,
sedan flytt.

**Ingår inte:** själva agent-loopen (T011).

## Definition of Done

- [ ] `to_openai_tools` är en ren funktion med tester; mappar name/description/
      parameters korrekt och bevarar `inputSchema` oförändrat.
- [ ] `apply_allowlist` failar hårt (`SystemExit`/tydlig exception) på okänt namn
      och listar både det okända och de tillgängliga (som idag).
- [ ] Tom beskrivning blir `""` (inte `None`) — kontraktet mot OpenAI-API:t.
- [ ] `main()` använder de utbrutna funktionerna; beteendet oförändrat.

## Testfall (skriv först)

1. `test_to_openai_tools_maps_fields` → mot fejk-MCP-serverns verktyg (T002):
   varje verktyg får `type=function`, rätt `name`, `parameters == inputSchema`.
2. `test_to_openai_tools_empty_description` → verktyg utan beskrivning → `""`.
3. `test_allowlist_filters_subset` → allow `{echo}` → exakt ett verktyg kvar.
4. `test_allowlist_unknown_fails_loudly` → allow `{finns_ej}` → fel som nämner
   `finns_ej` **och** de tillgängliga namnen.
5. `test_allowlist_none_returns_all` → `allow=None` → alla verktyg.

## Noteringar

Detta är ren refaktor under grönt: inga beteendeändringar, bara testbar struktur.
Kör testen, se dem gröna, commit:a litet.
