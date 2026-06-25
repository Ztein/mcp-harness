# T042 — seed-scenario: verktygsval under scoping/press

**Status:** DOING · **Fas:** E2E · **Prioritet:** P1 · **Beror på:** T040, T021

## Varför

PRD §2 och §11: menyns *storlek och innehåll* påverkar modellens verktygsval
(bevisat: scoping ändrade beteende). Detta scenario testar exakt det — kör samma
uppgift med (a) full verktygsmeny och (b) en snäv allowlist, och låter bedömaren
döma om scoping ändrade beteendet på ett begripligt sätt. Det validerar produktens
kärnpåstående: att den troget speglar harness-scoping.

## Omfattning

**Ingår:** ett scenario som körs i två varianter (full meny vs `--tools`-allowlist),
med kriterier som jämför verktygsval och svar mellan varianterna.

**Semantiska PASS/FAIL-kriterier**, t.ex.:
- Med full meny: väljer modellen ett vettigt verktyg för uppgiften?
- Med allowlist som *utesluter* det självklara verktyget: hanterar modellen det
  ärligt (säger att den inte kan) i stället för att hallucinera ett anrop?
- Speglar fingeravtrycket (T021) exakt den meny varianten skulle ge?

## Definition of Done

- [ ] Scenariofil med båda varianterna i T040:s format.
- [ ] Kriterier som tydligt fångar scoping-effekten.
- [ ] Agent-körda rapporter för båda varianterna, incheckade, med förbättringsspaning.

## Testfall (skriv först)

1. `test_scenario_scoping_parses` → filen parsas, båda varianterna fångas.
2. Agent-körning (E2E): kör båda varianterna, jämför, döm, notera förbättringar.

## Noteringar

Detta scenario är också en regression mot ”trogen verktygs-meny per profil/scoping”
(PRD §11 P1). Om allowlisten inte exakt speglas i menyn är det ett FAIL värt att
fånga tidigt.
