# T040 — E2E-scenarioformat + agent-driven körprocess

**Status:** TODO · **Fas:** E2E · **Prioritet:** P0 · **Beror på:** T022, T020, T044

## Varför

PRD §4 och §11: den **primära konsumenten** är en test-/QA-agent (människa eller
Claude) som kör protokoll-scenarier *som en människa skulle* och dömer PASS/FAIL
**semantiskt**. Vi vill ha scenarier som är skrivna som en mänsklig testare kunde
köra dem i CLI:t, med kriterier som en människa *eller* en LLM kan bedöma — och
där en del av testprocessen är att **identifiera förbättringsförslag**. Sedan kör
agenten dessa scenarier genom vårt CLI = riktiga E2E-tester som både fångar fel
och föder roadmappen.

Det här är inte ett auto-domar-ramverk (PRD §7 icke-mål). Det är en *struktur* för
mänsklig/agent-dömd körning — domen görs av en bedömare, verktyget bara kör och
loggar troget.

## Omfattning

**Ingår:**
- Ett **scenarioformat** (markdown) under `scenarios/`, läsbart och körbart av en
  människa eller agent. Varje scenario fångar: mål, förutsättningar (profil,
  servrar, modell), turer att mata in (som en användare skulle skriva), och
  **semantiska PASS/FAIL-kriterier**.
- Ett **rapportformat** som bedömaren (människa/agent) fyller i per körning:
  utfall per kriterium (PASS/FAIL + motivering) och en **förbättringsspaning**
  (konkreta förslag observerade under körningen).
- En tunn **körhjälp**: ett dokumenterat sätt att mata scenariots turer till CLI:t
  (piped stdin) och få JSONL + transkript + exit-kod tillbaka, så bedömaren har
  troget underlag att döma på.
- `scenarios/README.md` som beskriver formatet och hur agenten kör + rapporterar.

**Ingår inte:** automatisk PASS/FAIL-dömning av en LLM-domare i CI (det är ett
medvetet senare/valfritt steg, PRD §7 — får aldrig ersätta mänsklig dom).

## Definition of Done

- [ ] Scenario- och rapportformaten är dokumenterade i `scenarios/README.md` med
      ett ifyllt exempel.
- [ ] Minst tre seed-scenarier finns (T041–T043) i formatet.
- [ ] Körhjälpen tar ett scenario, matar dess turer till CLI:t (piped), och
      samlar JSONL + transkript + exit-kod till ett bedömnings-underlag.
- [ ] Underlaget innehåller **otrunkerade** verktygssvar (via T020) så semantisk
      dömning är möjlig.
- [ ] Rapportmallen har ett obligatoriskt **Förbättringsspaning**-avsnitt.

## Testfall (skriv först)

Körhjälpen testas mot fejk-LLM + test-MCP-över-HTTP (T044), och formatet
valideras mekaniskt:

1. `test_scenario_parses` → ett scenario-md parsas till mål, förutsättningar, turer,
   kriterier (ingen tyst förlust av ett kriterium).
2. `test_runner_feeds_turns_to_cli` → körhjälpen matar scenariots turer som piped
   stdin till en riktig CLI-process och fångar JSONL + exit-kod.
3. `test_underlag_has_untruncated_results` → bedömnings-underlaget bär hela
   verktygssvar (inte människo-vyns klipp).
4. `test_report_requires_improvement_section` → en rapport utan
   Förbättringsspaning flaggas som ofullständig.

## Noteringar

Den verkliga ”testkörningen” av denna ticket är att **agenten kör seed-scenarierna
genom CLI:t** och producerar riktiga rapporter — det är leveransen, inte bara
koden. Behåll ärligheten: en grön scenariokörning mot `raw`-profilen är inte
”verifierad i Intric” (approximation-not, PRD §11).
