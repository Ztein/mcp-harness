# T043 — seed-scenario: fel hanteras högljutt (fail-loudly)

**Status:** TODO · **Fas:** E2E · **Prioritet:** P1 · **Beror på:** T040, T012, T021

## Varför

Princip 3 (fail-hard, aldrig tyst) är produktens själ. Detta scenario testar att
harnessen — och MCP+modell genom den — failar *synligt* i de lägen som annars
tyst korrumperar en testkörning: ett verktyg som returnerar fel, ett svar med
flera content-block (T012-buggen), och en förväntnings-avvikelse (T021). En
människa/LLM ska kunna döma: ”syntes felet tydligt, eller maskerades det?”

## Omfattning

**Ingår:** ett scenario som avsiktligt provocerar (a) ett verktygsfel, (b) ett
verktygssvar med flera block, och (c) en `--expect-tools`-avvikelse — och kriterier
som dömer om varje fel blev *synligt och otvetydigt*.

**Semantiska PASS/FAIL-kriterier**, t.ex.:
- Vid verktygsfel: syns felet i transkript + JSONL, och fortsätter körningen
  begripligt (ingen tyst korruption)?
- Vid flerblockssvar: kommer **hela** svaret med (inget tyst tappat block)?
- Vid `--expect-tools`-avvikelse: failar körningen högljutt med exit≠0 och tydligt
  meddelande?

## Definition of Done

- [ ] Scenariofil i T040:s format som täcker de tre fail-lägena.
- [ ] Kriterier som dömer *synlighet* av fel, inte bara att fel uppstod.
- [ ] Agent-körd rapport incheckad, med förbättringsspaning.

## Testfall (skriv först)

1. `test_scenario_fail_loudly_parses` → filen parsas, alla tre lägen fångas.
2. Agent-körning (E2E): provocera felen genom CLI:t, döm synligheten, notera
   förbättringar.

## Noteringar

Detta scenario är det viktigaste regressionsskyddet i hela sviten: om något fel
någonsin börjar maskeras tyst ska detta scenario bli rött. Kör det ofta.
