# T002 — in-process fejk-MCP-server som fixtur

**Status:** TODO · **Fas:** 0 · **Prioritet:** P0 · **Beror på:** T001

## Varför

För att testa harnessens kärna (verktygslistning, verktygsanrop, schema-
presentation, svars-hantering) behöver vi en **riktig MCP-server** att tala med —
inte en mock av `ClientSession`. Mockar skulle dölja exakt de buggar vi bryr oss
om (t.ex. att bara `content[0]` läses, se T012). En liten in-process server som
exponerar kontrollerade verktyg ger oss ärlig täckning, enligt PRD §11
(”trogen verktygs-meny”, ”full verktygssvars-trohet”).

## Omfattning

**Ingår:** en fejk-MCP-server byggd på `mcp`-paketets server-API, ansluten via
in-memory streams (eller stdio) till en riktig `ClientSession`. Verktyg som
behövs för testerna:
- `echo(text)` → returnerar texten.
- `multi_block()` → returnerar **flera** content-block (för T012).
- `boom()` → kastar ett fel (för fel-vägen).
- `structured()` → returnerar JSON-struktur (för fält-assertion, PRD §11).

En pytest-fixtur som ger en initierad `ClientSession` kopplad till servern.

**Ingår inte:** Streamable-HTTP-transport mot riktig server (det är prod-vägen,
inte testvägen).

## Definition of Done

- [ ] Fixturen returnerar en **riktig** `ClientSession` som `initialize()`:ats mot
      den in-process servern.
- [ ] `session.list_tools()` returnerar de definierade verktygen.
- [ ] `session.call_tool("echo", {"text": "hej"})` returnerar "hej".
- [ ] Inget i fixturen mockar `ClientSession`, `call_tool` eller `list_tools`.

## Testfall (skriv först)

1. `test_fixture_lists_expected_tools` → `list_tools()` innehåller `echo`,
   `multi_block`, `boom`, `structured`.
2. `test_echo_roundtrips` → `call_tool("echo", {"text": "x"})` → "x".
3. `test_multi_block_returns_multiple_blocks` → `multi_block()` ger `len(content) > 1`
   (detta test bevisar att fixturen kan reproducera T012-buggen).
4. `test_boom_raises_or_returns_error` → `boom()` ger ett fel som klienten ser.

## Noteringar

Slå upp aktuellt server-API i `mcp`-paketet (dokumentationen kan ha ändrats —
använd doc-verktyget) innan du skriver fixturen. Håll servern minimal: den finns
bara för testerna, inte som ett exempel.
