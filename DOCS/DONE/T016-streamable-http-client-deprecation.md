# T016 — byt deprecerad streamablehttp_client → streamable_http_client

**Status:** DONE · **Fas:** 1 · **Prioritet:** P2 · **Beror på:** —

## Varför

Upptäckt under E2E-/testkörning: mcp varnar
`DeprecationWarning: Use streamable_http_client instead.` Den deprecerade
`streamablehttp_client` används i `cli.py` och `tests/test_http_mcp.py`. Att låta
en deprecation ligga i shippad kod driftar mot framtida mcp-versioner — fixa
tidigt medan ytan är liten.

## Omfattning

**Ingår:** byt importerna/anropen till `streamable_http_client` i `cli.py` och
testerna; bekräfta att signaturen är densamma; gör testsviten varningsfri (ev.
`filterwarnings = error` i pytest-config för att fail-hard på nya deprecations).

## Definition of Done

- [x] Ingen `DeprecationWarning` från `streamablehttp_client` i testkörningen.
- [x] CLI:t ansluter fortfarande (verifierat mot test-MCP över HTTP, T044).
- [x] Övervägt `filterwarnings = error` så framtida deprecations failar högljutt.

## Testfall (skriv först)

1. Kör `tests/test_http_mcp.py` med `-W error::DeprecationWarning` → grönt efter bytet.

## Noteringar

Litet städ. Om `filterwarnings = error` införs, gör det i egen commit så ev. andra
varningar kan adresseras separat.
