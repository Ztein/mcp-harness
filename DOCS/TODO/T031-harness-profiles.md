# T031 — harness-profiler

**Status:** TODO · **Fas:** 3 · **Prioritet:** P1 · **Beror på:** T011, T020, T030

## Varför

Produktens särdrag (PRD §5, Fas 2): en **harness-profil** beskriver hur en
specifik värd-harness presenterar MCP:er för sin modell — bas-systemprompt, hur
verktygsschemat presenteras, vilka servrar, modell+params, hur svar matas
tillbaka, scoping. En körning = profil + scenario. Profiler är **data** (en fil),
inte kod — användare kan skriva och dela egna.

## Omfattning

**Ingår:** profil-filformat som fångar tabellen i PRD §5; bas-ramning läggs *runt*
användarens skill; svars-presentations-/trunkeringsstrategi per profil; leverera
exempel-profiler `raw`, `generic-openai` (fler senare: `intric`, `claude-desktop`,
`cursor`). Profilen skrivs i JSONL-headern (T020). En **ärlig approximation-not**
i loggen när profilen skiljer sig från den riktiga harnessen (PRD §11 P2).

**Ingår inte:** att hävda 1:1-trohet mot en riktig harness — profiler bär
uttryckliga ”skiljer sig här”-noter (PRD §5, §10).

## Definition of Done

- [ ] Profil laddas från fil; `--profile <namn>` väljer den.
- [ ] Bas-ramning omsluter användarens skill **utan att skriva över den**.
- [ ] Menyn modellen ser speglar profilens scoping exakt (verifierat mot T021).
- [ ] Profilens namn + approximation-not skrivs i JSONL-headern.
- [ ] Minst `raw` (ingen extra ramning) och en till exempel-profil levereras.

## Testfall (skriv först)

1. `test_raw_profile_no_extra_framing` → `raw` → systemprompten är exakt skillen.
2. `test_profile_wraps_skill` → profil med bas-ramning → skillen finns kvar
   inbäddad, ramningen runt.
3. `test_profile_scoping_reflected_in_menu` → profil med allowlist → menyn +
   fingeravtryck speglar den.
4. `test_profile_recorded_in_jsonl_header` → headern bär profilnamn + not.

## Noteringar

Håll ”approximera”-ärligheten central: en grön terminal-körning får aldrig
misstas för ”verifierad i Intric”. Det är skillnaden mellan nyttigt och farligt.
