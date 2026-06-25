# T041 — seed-scenario: utforska en okänd MCP

**Status:** DOING · **Fas:** E2E · **Prioritet:** P1 · **Beror på:** T040

## Varför

PRD §4: ”den som utvärderar en främmande MCP — vill snabbt förstå vad en MCP gör
och hur robust den är, utan att koppla in den i sin riktiga miljö.” Detta är det
mest grundläggande mänskliga testflödet: en testare börjar med en server hen inte
känner och försöker förstå den genom samtal. Scenariot ska kännas som en riktig
människa som famlar sig fram.

## Omfattning

**Ingår:** ett scenario i T040:s format där en användare (1) frågar vad
assistenten kan, (2) ber den göra en grundläggande sak som kräver ett verktyg,
(3) ställer en uppföljning som kräver att resultatet från steg 2 används.

**Semantiska PASS/FAIL-kriterier** (bedömbara av människa/LLM), t.ex.:
- Förklarar assistenten sina förmågor utan att hitta på verktyg som inte finns?
- Väljer den ett *rimligt* verktyg för uppgiften (inte ett orelaterat)?
- Använder den faktiskt resultatet från föregående tur i uppföljningen?

## Definition of Done

- [ ] Scenariofil finns under `scenarios/` i T040:s format.
- [ ] Kriterierna är semantiska och bedömbara, inte sträng-exakta.
- [ ] En första **agent-körd rapport** finns incheckad (med förbättringsspaning).

## Testfall (skriv först)

1. `test_scenario_explore_parses` → filen parsas till giltigt scenario.
2. Agent-körning (manuell/E2E): kör scenariot genom CLI:t mot en riktig modell +
   test-MCP, fyll i rapporten, notera förbättringar. *Detta är själva leveransen.*

## Noteringar

Håll turerna i naturligt språk — som en människa skriver, inte som ett API-anrop.
Poängen är att fånga hur modell+MCP beter sig under verklig, luddig input.
