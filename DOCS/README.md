# DOCS — arbetstavla (tickets)

Det här är projektets arbetstavla. En **ticket = en markdown-fil** som rör sig
mellan tre mappar:

```
DOCS/
  TODO/    ← planerat, inte påbörjat
  DOING/   ← pågår nu (håll få samtidigt — helst 1)
  DONE/    ← klart, Definition of Done uppfylld
```

Att flytta en ticket = `git mv DOCS/TODO/T0XX-*.md DOCS/DOING/`. Statusraden i
filen uppdateras samtidigt. Historiken i git visar när varje ticket rörde sig.

## Arbetssätt (strikt TDD)

Det här projektet testar MCP-harnesses — alltså måste det självt hålla samma
disciplin som domänen det testar. Två regler styr allt:

1. **Testen skrivs först.** Varje ticket har ett avsnitt *Testfall*. Skriv ett
   rött test, se det faila, skriv minsta kod som gör det grönt, refaktorera.
   Ingen produktionskod utan ett test som krävde den.
2. **Testa på riktigt — fail loudly.** Inga mockar som döljer verkligheten. Vi
   kör mot en **riktig in-process fejk-MCP-server** och en **riktig HTTP-fejk-LLM**
   (canned svar över en faktisk socket), så att `urllib`- och MCP-klient-koden
   verkligen exekveras. Ett tyst halvresultat är värre än ett högljutt fel.

Dessa speglar PRD §8 (principer) och §11 (designvärden test-agenten kräver).

## Definition of Done — gäller varje ticket

Utöver ticketens egna DoD-punkter måste alltid följande hålla:

- [ ] Alla nya/ändrade beteenden täcks av tester som var **röda först**.
- [ ] `ruff check` och `ruff format --check` rena.
- [ ] `mypy` rent (strict där det är rimligt).
- [ ] Hela sviten grön i CI på en PR — inte bara lokalt.
- [ ] Ingen tyst trunkering eller svald exception införd (princip 3).
- [ ] Dokumentation uppdaterad om beteende mot användaren ändrats (README/PRD).

## Ticket-mall

```markdown
# T0XX — Kort titel

**Status:** TODO · **Fas:** N · **Prioritet:** P0/P1/P2 · **Beror på:** T0YY

## Varför
Problemet ticketen löser, med länk till PRD-avsnitt.

## Omfattning
Vad som ingår — och uttryckligen vad som *inte* gör det.

## Definition of Done
- [ ] Konkreta, verifierbara villkor.

## Testfall (skriv först)
1. Namngivet test → förväntat utfall.

## Noteringar
```

## Tavlan just nu

**Fas 0 — testfundament** (gör TDD möjligt; måste komma först)
- T001 — pytest-scaffolding + fejk-LLM över riktig HTTP
- T002 — in-process fejk-MCP-server som fixtur
- T003 — CI-pipeline (ruff, mypy, pytest)
- T004 — verktygskedja + LICENSE (ruff format, mypy, pre-commit)

**Fas 1 — refaktorera till testbara sömmar** (under gröna tester)
- T010 — bryt ut rena funktioner (schema-konvertering, allowlist)
- T011 — bryt ut agent-loopen till en testbar motor
- T012 — full verktygssvars-trohet: konkatenera ALLA content-block (buggfix)
- T013 — transkript-skrivare som injicerbar sink

**Fas 2 — kontraktsyta** (P0/P1 från test-agenten, PRD §11)
- T020 — JSONL-körlogg, versionerat schema, otrunkerat
- T021 — server-fingeravtryck + `--expect-tools` (fail-hard)
- T022 — headless exit-kod + enrads-sammanfattning
- T023 — tur-loop-broms + batch-resiliens

**Fas E2E — agent-driven scenariotestning** (PRD §4, §11, Fas 5)
- T044 — exponera test-MCP över HTTP för riktig E2E
- T040 — E2E-scenarioformat + agent-driven körprocess
- T041 — seed-scenario: utforska en okänd MCP
- T042 — seed-scenario: verktygsval under scoping/press
- T043 — seed-scenario: fel hanteras högljutt (fail-loudly)

**Fas 3 — roadmap** (PRD-faser 1–4)
- T030 — flera MCP-servrar via config
- T031 — harness-profiler
- T032 — fil-uppladdning
- T033 — observerbarhet+ (token/latens)

Ordningen är medveten: inget i Fas 1+ påbörjas innan Fas 0 ger ett grönt
testfundament. Fas 2 (kontraktsytan) prioriteras före Fas 3-funktioner, för det
är det test-agenten blockeras av idag.
