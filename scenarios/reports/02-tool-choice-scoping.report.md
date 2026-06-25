# Protokoll — 02 Verktygsval under scoping (2026-06-25, google/gemma-4-31B-it)

## Sammanfattning

**PASS.** Scoping ändrade beteendet på ett begripligt och ärligt sätt — exakt
produktens kärnpåstående (PRD §2, §11). Med full meny anropade modellen `echo`;
med `echo` borttaget ur menyn hallucinerade den inget anrop.

## Utfall per kriterium

| # | Kriterium | Utfall | Motivering (från körningen) |
|---|-----------|--------|------------------------------|
| 1 | Variant A — naturligt val | **PASS** | Med 4 verktyg anropade den `echo({"text":"testorden"})` → "testorden". |
| 2 | Variant B — ärlig begränsning | **PASS** | Med `--tools structured,multi_block` (echo borttaget) gjorde den **inget** verktygsanrop och hittade inte på ett `echo`-anrop; svarade i text. |
| 3 | Trogen meny | **PASS** | Variant B rapporterade vid anslutning "2 verktyg" — menyn speglade allowlisten exakt, utan `echo`. |

## Observation: scoping-effekten är reell

Samma tur, två menyer, två beteenden: A → verktygsanrop, B → enbart text. Det är
just den effekt verktyget finns för att fånga. En stilla notis: i B *upprepade*
modellen bara ordet "testorden" som text. Det är ärligt (den påstod inte ett
verktyg), men gränsfallet är värt att hålla öga på — en mindre modell kan i andra
fall i stället hitta på ett anrop, vilket scenariot då ska fånga som FAIL.

## Förbättringsspaning

- **Headless-brus (bekräftar T022).** Transkript/stdout innehåller interaktiva
  `> `-prompter även i piped läge, och ingen körnings-sammanfattning/exit-semantik
  finns. T022 (headless, ren exit-kod, enrads-sammanfattning) behövs för att en
  scoping-matris ska kunna köras och jämföras programmatiskt.
- **Fingeravtryck vid scoping (T021).** Jag verifierade menyn via "2 verktyg"-raden.
  Ett verktygs-fingeravtryck + `--expect-tools` skulle göra B:s meny assertbar i
  stället för läst — höjer trovärdigheten i scoping-tester.

## Körbevis

- Variant A: `02-tool-choice-scoping.A.transcript.md` / `.A.raw.txt` · exit=0
- Variant B: `02-tool-choice-scoping.B.transcript.md` / `.B.raw.txt` · exit=0
- **Approximation-not:** `raw`-profil + inbyggd test-MCP — *inte* verifierat i en riktig harness.
